package utils

import (
	"fmt"
	"github.com/npi-ai/npi/server/api"
	"github.com/npi-ai/npi/server/log"
	"os/exec"
)

func RunPython(file string, params map[string]string) error {
	args := []string{file}
	for k, v := range params {
		args = append(args, fmt.Sprintf("--%s", k), v)
	}
	cmd := exec.Command("python", args...)
	out, err := cmd.CombinedOutput()
	if err != nil {
		log.Warn().Str("output", string(out)).Msg("Failed to run python script")
		return api.ErrInternal.
			WithMessage("Failed to validate tools").WithError(err)
	}
	return nil
}
