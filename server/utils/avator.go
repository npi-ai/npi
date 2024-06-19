package utils

import (
	"bytes"
	"errors"
	"fmt"
	"github.com/ajstarks/svgo"
	"github.com/vincent-petithory/dataurl"
	"io"
	"math/rand"
	"time"
)

const (
	SvgDiameter = 24
	TextY       = 16
)

var (
	colors = []string{
		"#3AC86B", "#8864FF", "#5879FF", "#FAB608", "#FF6078",
		"#FF4CCA", "#FFA500", "#FF7F50", "#FF4500", "#FFD700",
	}
	seed = rand.New(rand.NewSource(time.Now().UnixNano()))
)

func GenerateAvatar(letter string) (io.Reader, error) {
	var b bytes.Buffer
	canvas := svg.New(&b)

	canvas.Start(SvgDiameter, SvgDiameter)
	canvas.Circle(SvgDiameter/2, SvgDiameter/2, SvgDiameter/2, fmt.Sprintf("fill:%s", colors[seed.Intn(len(colors))]))
	canvas.Text(SvgDiameter/2, TextY, letter, "text-anchor:middle;font-size:12px;fill:white")
	canvas.End()
	return &b, nil
}

func ParseDataURL(dataURL string) (*dataurl.DataURL, error) {
	obj, err := dataurl.DecodeString(dataURL)
	if err != nil {
		return nil, err
	}
	if obj.Type != "image" {
		return nil, errors.New("incorrect mime type")
	}
	if obj.Subtype == "" {
		obj.Subtype = "jpeg"
	}
	return obj, nil
}
