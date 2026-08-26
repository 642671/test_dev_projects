package main

import (
	"fmt"
	"os"

	"github.com/goretk/gore"
)

func main() {
	f, err := gore.Open(os.Args[1])
	if err != nil {
		panic(err)
	}
	defer f.Close()

	targets := map[uint64]bool{
		0x146c020: true,
		0x147d000: true,
		0x147c6e0: true,
		0x147cb20: true,
		0x147a860: true,
		0x1479860: true,
		0x14795d2: true,
		0x1479636: true,
		0x147e842: true,
		0x1483e50: true,
		0x4ad360: true,
		0x4b0520: true,
		0x503820: true,
		0x515340: true,
		0x14890a0: true,
		0x147d600: true,
	}

	all := []*gore.Package{}
	for _, getter := range []func() ([]*gore.Package, error){
		f.GetPackages,
		f.GetVendors,
		f.GetSTDLib,
		f.GetUnknown,
		f.GetGeneratedPackages,
	} {
		pkgs, err := getter()
		if err == nil {
			all = append(all, pkgs...)
		}
	}

	for _, p := range all {
		for _, fn := range p.Functions {
			if containsTarget(targets, fn.Offset, fn.End) {
				fmt.Printf("F 0x%x 0x%x %s\n", fn.Offset, fn.End, fn.Name)
			}
		}
		for _, m := range p.Methods {
			if containsTarget(targets, m.Offset, m.End) {
				fmt.Printf("M 0x%x 0x%x %s%s\n", m.Offset, m.End, m.Receiver, m.Name)
			}
		}
	}
}

func containsTarget(targets map[uint64]bool, start, end uint64) bool {
	for t := range targets {
		if t >= start && (end == 0 || t < end) {
			return true
		}
	}
	return false
}
