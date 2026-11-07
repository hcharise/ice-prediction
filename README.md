# Colorado Lake Ice Prediction
**Data Collection & Predictive Modeling Pipeline**

An end-to-end data science project to predict ice thickness on Colorado lakes using crowdsourced ice reports and historical weather data.

## Overview

Ice thickness is influenced by weather conditions, but reliable historical ice measurements are difficult to obtain. This project aims to address that gap by collecting publicly-shared ice reports, extracting structured observations, and combining them with historical weather data to develop a predictive model.

The project is being developed in stages, beginning with a Python-based web scraper to collect ice reports from a public Facebook page.

### Current Status and Limitations

**Status:** Initial data collection implemented and manually validated. Reliability improvements are ongoing.

The first phase focuses on collecting historical ice reports from the [Colorado Ice Conditions Facebook page](https://www.facebook.com/COIceconditions) using Python and Playwright. The scraper extracts Facebook posts and associated comments, including content loaded dynamically through scrolling.

Manual validation has confirmed that the scraper generally captures the expected records without substantial duplication or silent omissions, though some posts still produce extraction errors (approximately 10% during recent testing). These errors are logged, and the scraper is designed to continue processing subsequent posts rather than terminating the entire run.

Known limitations include:
- Not all posts can be extracted successfully.
- Complete extraction of nested comment replies is not supported.
- Changes to Facebook's HTML structure or loading behavior may require adjustments to the scraper.

The current implementation is suitable for the project's initial data collection and exploratory analysis phases, with additional validation planned as the dataset grows.

### Technical Challenges

Facebook's dynamically changing page structure presents several challenges, including DOM elements that are replaced during scrolling, inconsistent content structures, and browser automation timeouts.

Development has focused on handling these challenges through incremental debugging, dynamic element selection, and separating browser automation from extraction and parsing logic.

## Setup and Usage

### Prerequisites

- Python 3.9 or later
- Git
- Chromium (installed through Playwright)
- A Facebook account for manually logging in, if prompted

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/hcharise/ice-prediction.git
   cd ice-prediction
   ```

2. Create and activate a Python virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

   On Windows, use `.venv\Scripts\activate` instead.

3. Install project dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

4. Install the Chromium browser used by Playwright:

   ```bash
   python -m playwright install chromium
   ```

### Running the Scraper

With the virtual environment activated, run:

```bash
python facebook_scraper.py
```

The scraper opens the Colorado Ice Conditions Facebook page in Chromium. Follow the terminal prompts to log in manually if needed and confirm when the browser is ready.

The scraper extracts posts and associated comments and saves the results to `facebook_posts.json` and `facebook_comments.json`.

Follow the terminal prompts to close the browser when processing is complete.

### Output

The scraper generates two JSON files in the project directory:

- `facebook_posts.json` — Extracted post text, timestamps, post IDs, and URLs.
- `facebook_comments.json` — Extracted comment text, timestamps, comment IDs, and associated post IDs.

These files provide the raw data for subsequent processing, including identifying lake names, observation dates, and reported ice thickness.

### Example Data

The [`examples/`](examples/) directory contains small, synthetic JSON datasets demonstrating the scraper's output structure.

- [`sample_posts.json`](examples/sample_posts.json) — Example Facebook post records.
- [`sample_comments.json`](examples/sample_comments.json) — Example comment records associated with those posts.

These examples use fictional content and identifiers to demonstrate the data format without publishing actual Facebook user information.

Raw scraped data is excluded from version control.

## Project Roadmap

- [x] Implement initial post extraction
- [x] Implement initial comment and reply extraction
- [ ] Improve scraper reliability and expand nested reply extraction
- [ ] Extract structured lake, date, and ice thickness observations
- [ ] Integrate historical weather data
- [ ] Develop and evaluate predictive models

## Technologies

**Current:** Python, Playwright, JSON, Git/GitHub

**Planned:** pandas, weather data APIs, scikit-learn

### Development Approach

This project was developed with assistance from ChatGPT for debugging, troubleshooting, and exploring implementation approaches. AI-generated suggestions were reviewed, tested, and adapted throughout development, with an emphasis on understanding the underlying code and technical decisions.
