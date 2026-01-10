# bsport.list_offers

## Description

Fetch upcoming class offers from the bsport scheduling API for a specific company id. The capability applies time-window, availability, activity, and coach filters, and returns a normalized summary (or raw offers when requested).

## Non-goals

- Booking or reserving classes
- Authentication or payment workflows
- Caching or persistence of offers
- Timezone conversions beyond UTC normalization
- Formatting schedules for presentation (that is adapter/UI work)

## Deterministic behavior

Given the same inputs and the same upstream API responses at the time of execution, the capability returns the same output shape and filtering results. No hidden prompting or interactive behavior is used.
