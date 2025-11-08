# TODO: Implement "Get Help (SOS)" Feature

## Database Extensions
- [ ] Add functions in `utils/firebase_service.py` to store/retrieve volunteer profiles (collection 'volunteers').
- [ ] Add functions in `utils/mongo_service.py` to store/retrieve volunteer profiles (collection 'volunteers').

## Demo Data
- [ ] Add sample volunteer profiles in `data/demo_data.py` with name, district/area, languages, contact, availability.

## Volunteer Features
- [ ] Extend `components/auth.py` to support volunteer login (differentiate from farmers using user_type).
- [ ] Update `components/tech_portal.py` to include:
  - [ ] Profile management (edit name, district, languages, contact).
  - [ ] Availability toggle (Online/Offline).
  - [ ] View incoming help requests from nearby farmers.
  - [ ] Notifications for new requests (UI-based).

## Farmer SOS Enhancements
- [ ] Modify `components/sos.py` to add the new "Get Help" feature:
  - [ ] Button: “Need Help? Connect with a Volunteer”.
  - [ ] Automatic location detection using map_select_ui (lat/lon), mock reverse geocode to district/village.
  - [ ] Matching logic: Find volunteers in same/nearest area, prioritize by language.
  - [ ] If matched: Show volunteer name, contact, "Call Volunteer" button.
  - [ ] If no match: Show “No nearby volunteer found. Connecting you via call.” (mock call).
  - [ ] "Report Issue" button to escalate.
  - [ ] After session: Feedback rating (1-5 stars), option to escalate unresolved issues.

## Matching Logic
- [ ] Implement distance calculation (simple Euclidean) and prioritization in `components/sos.py` or a new helper in `utils/helpers.py`.
- [ ] Mock languages: English, Hindi, Telugu.

## UI/UX and Integration
- [ ] Ensure user context (farmer/volunteer) is handled via session state.
- [ ] Mock SMS/calls for demo.
- [ ] Update `app.py` if needed for navigation or user type selection.

## Testing and Followup
- [ ] Test the app locally to ensure matching works.
- [ ] Verify DB logging in demo mode.
- [ ] If real DB, ensure collections are created.
- [ ] Add any missing imports or error handling.
