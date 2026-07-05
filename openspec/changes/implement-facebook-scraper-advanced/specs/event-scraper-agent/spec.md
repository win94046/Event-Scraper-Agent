## MODIFIED Requirements

### Requirement: Event Web Scraping with Cache
#### Scenario: Google Search Dorking for Facebook Events
- **WHEN** the scraper is executed for Facebook with the user's keywords and filters
- **THEN** the system SHALL construct a Google Search URL containing the dork query (e.g., `site:facebook.com (keywords...) ("研討會"...) "台北"`) and the time range parameter (e.g., `&tbs=qdr:w` for past week)
- **AND** the system SHALL crawl the Google SERP using Playwright to extract search results (title, link, and snippet)
- **AND** the system SHALL format the extracted results as a raw text string, cache it locally using the MD5 of the Google Search URL, and return it

#### Scenario: Cache Hit with TTL Check
- **WHEN** a cache file exists for the target URL
- **AND** the file's modification age is less than the configured Cache TTL (e.g., 24 hours)
- **THEN** the system SHALL load the content directly from the local cache file
- **AND** if the cache age exceeds the TTL, the system SHALL discard the cache, fetch fresh data from the web, and overwrite the cache

#### Scenario: CAPTCHA Triggered Circuit Breaker
- **WHEN** the system navigates to Google Search and encounters a CAPTCHA wall (e.g., redirect to `google.com/sorry/index`) or is blocked with HTTP status 429
- **THEN** the system SHALL immediately log a critical error, raise a block exception, and halt all subsequent search queries in the batch

#### Scenario: Batch Query Limiting
- **WHEN** a user's subscription contains multiple keywords that would normally trigger many individual search queries
- **THEN** the system SHALL group keywords using Boolean `OR` constraints to restrict the total number of Google Search queries per batch to a maximum limit (e.g., 3 queries)

### Requirement: LLM Extraction with Structured Outputs
#### Scenario: Event Extraction from Google Search Snippets
- **WHEN** raw text composed of Google Search result titles and snippets is passed to the LLM processor
- **THEN** the system SHALL provide the current crawl timestamp as context to the LLM
- **AND** the LLM SHALL parse the snippets to extract standard event structures (e.g., title, datetime, location, source URL)
- **AND** the LLM SHALL resolve relative times mentioned in snippets (e.g., "3 days ago") using the current crawl timestamp as a reference

### Requirement: Keyword Matching and Email Notification
#### Scenario: URL Tracking Parameters Stripped Before Deduplication
- **WHEN** a newly extracted event URL is processed for deduplication
- **THEN** the system SHALL clean the URL by removing tracking query parameters (such as `fbclid`, `utm_source`, `utm_medium`, `utm_campaign`, etc.)
- **AND** the system SHALL calculate the SHA256 hash using the cleaned URL to check against `sent_events.json`
