package main

import (
	"bufio"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path"
	"regexp"
	"strings"
	"time"
)

const (
	maxOfInt64      = 9223372036854775807
	datetimePattern = "^\\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1]) ([0-1][0-10]|2[0-3]):([0-5][0-9]):([0-5][0-9])(,|\\.)\\d{3}"
)

type StoredStatusData struct {
	ModDateTime int64 `json:"modification_datetime"`
	Size        int64 `json:"size"`
	Position    int64 `json:"position"`
}

type FileStatus struct {
	Name    string
	Rotated bool
	StoredStatusData
}

func (fs *FileStatus) Init(inFileName string) {
	fs.Name = strings.ReplaceAll(inFileName, ".log", ".json")
}

func (fs *FileStatus) Reset() {
	fs.ModDateTime = 0
	fs.Size = maxOfInt64
	fs.Position = 0
	fs.Rotated = false
}

func (fs *FileStatus) Load() {
	var prevFileData StoredStatusData
	statusDataRaw, errReadStatus := os.ReadFile(fs.Name)
	if errReadStatus != nil {
		fmt.Printf("No status file '%v' assuming first run\n", fs.Name)
		fs.Reset()
	} else {
		errMarshal := json.Unmarshal(statusDataRaw, &prevFileData)
		if errMarshal != nil {
			fmt.Printf(
				"Problem with decoding stored modification timestamp and file size assuming first run: %v\n",
				errMarshal,
			)
			fs.Reset()
		} else {
			fs.ModDateTime = prevFileData.ModDateTime
			fs.Size = prevFileData.Size
			fs.Position = prevFileData.Position
		}
	}
}

func (fs FileStatus) Save() {
	statusJson, mErr := json.Marshal(fs.StoredStatusData)
	if mErr != nil {
		fmt.Printf("Problem %v with marshalling the following data %v\n", mErr, fs)
	} else {
		wErr := os.WriteFile(fs.Name, statusJson, 0660)
		if wErr != nil {
			fmt.Printf("Problem '%v' when saving status file '%v'\n", wErr, fs.Name)
		}
	}

}

func printLines(lins []string) {
	for _, ll := range lins {
		fmt.Println(ll)
	}
}

func processLines(inLines []string) []string {
	datetimeRegexp, _ := regexp.Compile(datetimePattern)
	mergingJson := false
	jsonLines := []string{}
	repairedLines := []string{}
	messageBeforeJson := ""
	for _, lineContent := range inLines {
		if datetimeRegexp.MatchString(lineContent) && strings.HasSuffix(lineContent, "{") {
			mergingJson = true
			jsonLines = append(jsonLines, "{")
			messageBeforeJson = lineContent[:len(lineContent)-2]
		} else {
			if mergingJson {
				jsonLines = append(jsonLines, lineContent)
			} else {
				repairedLines = append(repairedLines, lineContent)
			}
		}
		endOfJson := false
		if lineContent == "}" {
			endOfJson = true
		}
		if endOfJson {
			mergingJson = false
			jsonRawText := []byte(strings.Join(jsonLines, ""))
			var jsonData *interface{}
			errUnmar := json.Unmarshal(jsonRawText, &jsonData)
			var jsonBytes []byte
			if errUnmar == nil {
				jsonBytes, _ = json.Marshal(jsonData)
			}
			repairedLines = append(
				repairedLines,
				fmt.Sprintf(
					"%v%v",
					messageBeforeJson,
					string(jsonBytes),
				),
			)
			jsonLines = []string{}
			messageBeforeJson = ""
		}
	}
	fmt.Println(" ---- repairedLines ----")
	printLines(repairedLines)
	return repairedLines
}

func main() {
	checkCycle := flag.Int(
		"cycle",
		1,
		"Check cycle in seconds",
	)
	inputFilePath := flag.String(
		"inFile",
		"../in-files/broken.log",
		"Input file with broken logs",
	)
	outputDirPath := flag.String(
		"outDir",
		"../out-files",
		"Output directory with repaired logs",
	)
	// rotadedFiles := flag.Int(
	// 	"rotFiles",
	// 	0,
	// 	"Number of extra files generated by log rotation",
	// )
	flag.Parse()
	var sleepTime time.Duration = time.Duration(*checkCycle) * time.Second
	_, inputFileName := path.Split(*inputFilePath)
	outputFilePath := strings.Join(
		[]string{
			*outputDirPath,
			inputFileName,
		},
		"/",
	)
	var prevFileStatus FileStatus
	prevFileStatus.Init(inputFileName)
	for {
		time.Sleep(sleepTime)
		fmt.Println("_________________________________________________")
		prevFileStatus.Load()
		fmt.Printf("Previous saved file status: %+v\n", prevFileStatus.StoredStatusData)
		fileInfo, errStat := os.Stat(*inputFilePath)
		if errStat != nil {
			fmt.Printf(
				"Problem '%v' during checking log file '%v' status\n",
				errStat,
				*inputFilePath,
			)
		} else {
			currentModTime := fileInfo.ModTime().Unix()
			currentSize := fileInfo.Size()
			if currentModTime > int64(prevFileStatus.ModDateTime) {
				fmt.Printf(
					"File updated at '%v' and has size '%v'\n",
					fileInfo.ModTime().Unix(),
					fileInfo.Size(),
				)
				file, errOpen := os.Open(*inputFilePath)
				if errOpen != nil {
					fmt.Println("Can't open file. Waiting to next cycle")
					continue
				}
				scanner := bufio.NewScanner(file)
				scanner.Split(bufio.ScanLines)
				lines := []string{}
				var lineIndex int64 = 0
				for scanner.Scan() {
					ltc := scanner.Text()
					lineIndex++
					if lineIndex <= prevFileStatus.Position {
						continue
					}
					lines = append(lines, ltc)
				}
				if len(lines) > 0 {
					var procLines []string
					prevFileStatus.Position = lineIndex
					procLines = processLines(lines)
					if len(procLines) > 0 {
						fmt.Println(outputFilePath)
						writeFile, errOpenWr := os.OpenFile(
							outputFilePath,
							os.O_CREATE|os.O_APPEND|os.O_WRONLY,
							0644,
						)
						if errOpenWr != nil {
							fmt.Println("Open to write error:", errOpenWr)
						}
						defer writeFile.Close()
						for _, ltw := range procLines {
							if _, errWri := writeFile.WriteString(ltw + "\n"); errWri != nil {
								fmt.Println("Write error", errWri)
							}
						}
					}
				}
				if currentSize < prevFileStatus.Size {
					prevFileStatus.Rotated = true
					prevFileStatus.Position = 0
				}
				if prevFileStatus.Rotated {
					fmt.Printf("File rotated %v\n", prevFileStatus.Rotated)
				} else {
					fmt.Print("\n")
				}
				prevFileStatus.ModDateTime = currentModTime
				prevFileStatus.Size = currentSize
				prevFileStatus.Rotated = false
				prevFileStatus.Save()
			} else {
				fmt.Print("\n\n")
			}
		}
	}

}