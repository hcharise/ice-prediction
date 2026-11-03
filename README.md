# Colorado Lake Ice Prediction
**Data Collection & Predictive Modeling Pipeline**

An end-to-end data science project to predict ice thickness on Colorado lakes using crowdsourced ice reports and historical weather data.

## Overview

Ice thickness is influenced by weather conditions, but reliable historical ice measurements are difficult to obtain. This project aims to address that gap by collecting publicly-shared ice reports, extracting structured observations, and combining them with historical weather data to develop a predictive model.

The project is being developed in stages, beginning with a Python-based web scraper to collect ice reports from a public Facebook page.

## Current Implementation: Data Collection

**Status: Functional prototype — debugging and refactoring in progress**

The first phase focuses on collecting historical ice reports from the [Colorado Ice Conditions Facebook page](https://www.facebook.com/COIceconditions) using Python and Playwright.

The scraper is designed to:

- Navigate dynamically loaded Facebook content, including a virtualized feed.
- Identify and extract posts while avoiding duplicate processing.
- Expand truncated posts to capture complete text.
- Extract post timestamps and available metadata.
- Parse comments, including timestamps, comment IDs, and associated post IDs.
- Store extracted data in JSON format for downstream processing.

### Technical Challenges

Facebook's dynamically changing page structure presents several challenges, including DOM elements that are replaced during scrolling, inconsistent content structures, and browser automation timeouts.

Development has focused on handling these challenges through incremental debugging, dynamic element selection, and separating browser automation from extraction and parsing logic.

## Project Roadmap

- [x] Implement initial post extraction
- [x] Implement initial comment and reply extraction
- [ ] Complete scraper debugging, validation, and refactoring
- [ ] Extract structured lake, date, and ice thickness observations
- [ ] Integrate historical weather data
- [ ] Develop and evaluate predictive models

## Technologies

**Current:** Python, Playwright, JSON, Git/GitHub

**Planned:** pandas, weather data APIs, scikit-learn

### Development Approach

This project was developed with assistance from ChatGPT for debugging, troubleshooting, and exploring implementation approaches. AI-generated suggestions were reviewed, tested, and adapted throughout development, with an emphasis on understanding the underlying code and technical decisions.
