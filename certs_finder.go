package main

import (
	"bufio"
	"context"
	"crypto/ecdsa"
	"crypto/rsa"
	"crypto/tls"
	"crypto/x509"
	"encoding/csv"
	"flag"
	"fmt"
	"net"
	"net/http"
	"os"
	"sort"
	"strings"
	"sync"
	"time"
)

var (
	insecureAlgorithms = map[x509.SignatureAlgorithm]string{
		x509.MD2WithRSA:        "MD2",
		x509.MD5WithRSA:        "MD5",
		x509.SHA1WithRSA:       "SHA1",
		x509.DSAWithSHA1:       "DSA-SHA1",
		x509.ECDSAWithSHA1:     "ECDSA-SHA1",
		x509.SHA256WithRSAPSS:  "RSAPSS-SHA256",
		x509.SHA384WithRSAPSS:  "RSAPSS-SHA384",
		x509.SHA512WithRSAPSS:  "RSAPSS-SHA512",
	}
	portStr     string
	workerCount int
	timeout     time.Duration
	retries     int
	batchSize   int
)

func main() {
	flag.StringVar(&portStr, "ports", "443,8443,465,993,995,22", "Comma-separated list of ports")
	flag.IntVar(&workerCount, "workers", 1000, "Concurrent workers")
	flag.DurationVar(&timeout, "timeout", 5*time.Second, "Connection timeout")
	flag.IntVar(&retries, "retries", 1, "Connection retries")
	flag.IntVar(&batchSize, "batch", 10000, "Batch buffer size")
	flag.Parse()

	portList := strings.Split(portStr, ",")
	ipChan := make(chan string, batchSize)
	resultChan := make(chan []string, batchSize)

	// Start result writer
	go writeResults(resultChan)

	// Start port scanners
	var wg sync.WaitGroup
	for _, port := range portList {
		wg.Add(1)
		p := strings.TrimSpace(port)
		go func(port string) {
			defer wg.Done()
			startPortWorkers(ipChan, resultChan, port)
		}(p)
	}

	// Feed IPs from stdin
	scanner := bufio.NewScanner(os.Stdin)
	for scanner.Scan() {
		ipChan <- strings.TrimSpace(scanner.Text())
	}
	close(ipChan)

	wg.Wait()
	close(resultChan)
}

func startPortWorkers(ipChan <-chan string, resultChan chan<- []string, port string) {
	var wg sync.WaitGroup
	workerPool := make(chan struct{}, workerCount/len(portList))

	for ip := range ipChan {
		workerPool <- struct{}{}
		wg.Add(1)

		go func(ip, port string) {
			defer func() {
				<-workerPool
				wg.Done()
			}()

			processIPPort(ip, port, resultChan)
		}(ip, port)
	}

	wg.Wait()
}

func processIPPort(ip, port string, resultChan chan<- []string) {
	target := net.JoinHostPort(ip, port)
	var cert *x509.Certificate
	var tlsVersion string

	client := &http.Client{
		Transport: &http.Transport{
			TLSClientConfig: &tls.Config{
				InsecureSkipVerify: true,
				MinVersion:         tls.VersionTLS12,
				MaxVersion:         tls.VersionTLS13,
			},
			DialTLSContext: func(ctx context.Context, network, addr string) (net.Conn, error) {
				conn, err := tls.Dial(network, addr, &tls.Config{
					InsecureSkipVerify: true,
				})
				if conn != nil {
					tlsVersion = tlsVersionToString(conn.ConnectionState().Version)
				}
				return conn, err
			},
		},
		Timeout: timeout,
	}

	for attempt := 0; attempt <= retries; attempt++ {
		ctx, cancel := context.WithTimeout(context.Background(), timeout)
		defer cancel()

		req, _ := http.NewRequestWithContext(ctx, "GET", "https://"+target, nil)
		resp, err := client.Do(req)

		if err == nil {
			defer resp.Body.Close()
			if resp.TLS != nil && len(resp.TLS.PeerCertificates) > 0 {
				cert = resp.TLS.PeerCertificates[0]
				break
			}
		}
	}

	if cert != nil {
		resultChan <- formatResult(ip, port, cert, tlsVersion)
	}
}

func tlsVersionToString(version uint16) string {
	switch version {
	case tls.VersionTLS13:
		return "TLS1.3"
	case tls.VersionTLS12:
		return "TLS1.2"
	case tls.VersionTLS11:
		return "TLS1.1"
	default:
		return "UNKNOWN"
	}
}

func formatResult(ip, port string, cert *x509.Certificate, tlsVersion string) []string {
	domains := make(map[string]struct{})
	if cert.Subject.CommonName != "" {
		domains[cert.Subject.CommonName] = struct{}{}
	}
	for _, dns := range cert.DNSNames {
		domains[dns] = struct{}{}
	}

	var insecureReasons []string
	now := time.Now()

	// Certificate validity
	if now.After(cert.NotAfter) {
		insecureReasons = append(insecureReasons, "expired")
	}
	if now.Before(cert.NotBefore) {
		insecureReasons = append(insecureReasons, "not_valid_yet")
	}

	// Signature algorithm
	if alg, exists := insecureAlgorithms[cert.SignatureAlgorithm]; exists {
		insecureReasons = append(insecureReasons, "weak_algorithm:"+alg)
	}

	// Key strength
	switch pub := cert.PublicKey.(type) {
	case *rsa.PublicKey:
		if pub.Size() < 256 { // 2048 bits
			insecureReasons = append(insecureReasons,
				fmt.Sprintf("weak_rsa_key:%d_bits", pub.Size()*8))
		}
	case *ecdsa.PublicKey:
		if pub.Params().BitSize < 256 {
			insecureReasons = append(insecureReasons,
				fmt.Sprintf("weak_ec_key:%d_bits", pub.Params().BitSize))
		}
	}

	// Chain issues
	if len(cert.IssuingCertificateURL) == 0 {
		insecureReasons = append(insecureReasons, "no_issuer_url")
	}

	// TLS version
	if tlsVersion == "TLS1.1" || tlsVersion == "UNKNOWN" {
		insecureReasons = append(insecureReasons, "weak_protocol:"+tlsVersion)
	}

	// Sort domains
	domainList := make([]string, 0, len(domains))
	for d := range domains {
		domainList = append(domainList, d)
	}
	sort.Strings(domainList)

	return []string{
		ip,
		port,
		strings.Join(domainList, ","),
		cert.NotAfter.Format(time.RFC3339),
		cert.Issuer.String(),
		strings.Join(insecureReasons, "|"),
		tlsVersion,
	}
}

func writeResults(results <-chan []string) {
	w := csv.NewWriter(os.Stdout)
	defer w.Flush()

	// Write header
	w.Write([]string{"ip", "port", "domains", "expiry", "issuer", "insecure", "tls_version"})

	for record := range results {
		w.Write(record)
		w.Flush()
	}
}
