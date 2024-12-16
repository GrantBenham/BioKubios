# BioKubios - Biopac Data Processing Tool for Kubios HRV

BioKubios is a Python-based graphical interface tool designed to streamline the processing of Biopac (.acq) files and prepare data for Kubios HRV analysis.

## Features

### 1. Read Function
- View markers and their timestamps from multiple .acq files
- Display original UTC times and UTC adjusted times
- Calculate relative times from Segment 1 marker
- Supports multiple file processing simultaneously

### 2. Extract Function
- Extract marker timings from .acq files
- Handle duplicate markers through interactive resolution
- Export data to CSV format
- Automatic detection and handling of problematic markers
- Preserves original marker order

### 3. Kubios Function
- Convert extracted data to Kubios-compatible format
- Customize section durations and timing buffers
- Color-code different sections
- Generate Kubios_Samples.csv for automated sample generation

## Requirements

- Python 3.x
- Required Python packages:
  - bioread
  - tkinter
  - dateutil
  - csv
  - datetime
  - os
  - sys

## Installation

1. Clone the repository:
git clone https://github.com/GrantBenham/biokubios.git

2. Install required packages:
```bash
pip install bioread python-dateutil
```

## Usage

1. Run the main script:
```bash
python biokubios.py
```

2. Use the graphical interface to:
   - Read and view Biopac markers
   - Extract marker data to CSV
   - Convert data to Kubios format

## Interface Guide

### Main Window
- **Read**: View markers and timestamps from .acq files
- **Extract**: Extract marker data to CSV format
- **Kubios**: Convert data to Kubios-compatible format

### Read Function
1. Select UTC offset
2. Choose .acq files
3. View marker information in a table format

### Extract Function
1. Select .acq files
2. Resolve any duplicate markers if present
3. Review output.csv file

### Kubios Function
1. Select output.csv file
2. Configure section settings:
   - Duration
   - Timing buffer
   - Color coding
3. Generate Kubios_Samples.csv

## File Formats

### Input
- Biopac (.acq) files

### Output
- output.csv: Contains extracted marker data
- Kubios_Samples.csv: Formatted for Kubios HRV analysis

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

MIT License

Copyright (c) 2024 [Grant Benham]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Authors

Grant Benham   

## Acknowledgments

- Bioread library developers
- Kubios HRV software team
