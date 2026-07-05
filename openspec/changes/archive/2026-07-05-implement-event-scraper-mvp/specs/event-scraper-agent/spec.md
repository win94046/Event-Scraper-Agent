## ADDED Requirements

### Requirement: Event Web Scraping with Cache
The system SHALL crawl tech event platforms (specifically Accupass and Facebook) using Playwright asynchronously. The system SHALL support auto-scrolling to load dynamic posts. The system SHALL support caching pages locally, saving/reading the raw text of successfully loaded pages.

#### Scenario: Cache Hit on Scraper Run
- **WHEN** the scraper is executed with cache enabled and a cached file exists for the target URL
- **THEN** the system SHALL load the content directly from the local cache directory instead of launching Playwright

#### Scenario: Cache Miss and Playwright Scrape
- **WHEN** the scraper is executed and no cache exists for the target URL
- **THEN** the system SHALL launch Playwright asynchronously, crawl the page, scroll the page to load dynamic content, and write the raw text to the local cache directory

### Requirement: LLM Extraction with Structured Outputs
The system SHALL parse the crawled raw text using Gemini LLM API and structured outputs. The API response SHALL strictly follow the Pydantic schema for tech events. Non-event texts SHALL be filtered out with `is_event` set to false.

#### Scenario: Successful Tech Event Extraction
- **WHEN** raw text of a valid tech event is passed to the LLM processor
- **THEN** the system SHALL return a JSON dictionary matching the Standard Event Schema with `is_event` set to true

#### Scenario: Irrelevant Text Filtering
- **WHEN** raw text of a normal, non-event post is passed to the LLM processor
- **THEN** the system SHALL return a JSON dictionary with `is_event` set to false

### Requirement: Keyword Matching and Email Notification
The system SHALL match extracted events with user keywords. The system SHALL filter out duplicate events that exist in `sent_events.json`. The system SHALL send custom HTML emails containing matched events to the user using SMTP.

#### Scenario: Match and Deduplicate Email Sending
- **WHEN** a user is subscribed to specific keywords and a new matching event is extracted (and not found in sent_events.json)
- **THEN** the system SHALL send a custom HTML email to the user's email, and update `sent_events.json` with the event's URL hash

### Requirement: Logging and Traceability
The system SHALL configure a standard logging mechanism. The system SHALL log all critical events, system progress, warnings, and errors. The logs SHALL be outputted to the standard output and saved to a local rolling file. The system SHALL log detailed exception stack traces on critical failures (such as SMTP connection failure or LLM API error) to allow troubleshooting.

#### Scenario: Exception Logged on Failure
- **WHEN** a critical system error occurs during the execution of any module (Scraper, LLM, or SMTP)
- **THEN** the system SHALL capture the exception and write the error message along with the detailed traceback stack to the local log file
