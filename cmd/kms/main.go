package main

import (
	"os"

	"github.com/tfbi/kms-cli/internal/gokms"
)

func main() {
	os.Exit(gokms.Run(os.Args[1:], nil, os.Stdin, os.Stdout, os.Stderr))
}
