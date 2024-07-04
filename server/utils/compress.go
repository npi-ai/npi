package utils

import (
	"archive/zip"
	"io"
	"os"
	"path/filepath"
	"strings"
)

func ExtractZip(src, dest string) error {
	r, err := zip.OpenReader(src)
	if err != nil {
		return err
	}
	defer r.Close()

	_ = os.MkdirAll(dest, os.ModePerm)

	for _, f := range r.File {
		fpath := filepath.Join(dest, f.Name)

		if f.FileInfo().IsDir() {
			// Make Folder
			_ = os.MkdirAll(fpath, os.ModePerm)
		} else {
			// Make File
			if err = os.MkdirAll(filepath.Dir(fpath), os.ModePerm); err != nil {
				return err
			}

			outFile, err := os.OpenFile(fpath, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, f.Mode())
			if err != nil {
				return err
			}

			rc, err := f.Open()
			if err != nil {
				return err
			}

			_, err = io.Copy(outFile, rc)

			// Close the file without deferring to handle errors properly
			outFile.Close()
			_ = rc.Close()

			if err != nil {
				return err
			}
		}
	}
	return nil
}

// addToZip adds a file or directory to the zip writer
func addToZip(zipWriter *zip.Writer, filePath, basePath string) error {
	fileInfo, err := os.Stat(filePath)
	if err != nil {
		return err
	}

	// Create a zip header based on file info
	header, err := zip.FileInfoHeader(fileInfo)
	if err != nil {
		return err
	}

	// Ensure the header's Name does not include the basePath
	header.Name = strings.TrimPrefix(filePath, basePath+"/")

	// Use deflate to better compress files that are not compressed
	header.Method = zip.Deflate

	// Check if it's a directory
	if fileInfo.IsDir() {
		header.Name += "/" // append a slash for directories
	} else {
		// Add the file to the zip
		writer, err := zipWriter.CreateHeader(header)
		if err != nil {
			return err
		}
		file, err := os.Open(filePath)
		if err != nil {
			return err
		}
		defer file.Close()
		_, err = io.Copy(writer, file)
		return err
	}
	return nil
}

// ZipDir recursively zips the contents of a directory
func ZipDir(dirPath, zipPath string) error {
	// Create the output zip file
	outFile, err := os.Create(zipPath)
	if err != nil {
		return err
	}
	defer outFile.Close()

	// Create a new zip archive writer
	zipWriter := zip.NewWriter(outFile)
	defer zipWriter.Close()

	// Walk the directory
	//basePath := filepath.Dir(dirPath)
	err = filepath.Walk(dirPath, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		return addToZip(zipWriter, path, dirPath)
	})

	return err
}
