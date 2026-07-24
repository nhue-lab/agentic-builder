# Task List: Phase 4 (Retry résilient)

- [x] 1. Add `tenacity>=8.2.0` to `pyproject.toml` dependencies.
- [x] 2. Install tenacity in the virtual environment.
- [x] 3. Create/update `implementation_plan.md` to define the design for resilient retries.
- [x] 4. Modify `src/lms/router.py` to import `tenacity` and implement the async retry logic with exponential backoff on transient errors.
- [x] 5. Run existing tests to ensure no regression.
- [x] 6. Write unit tests to verify the retry and fallback mechanism.
- [x] 7. Update `walkthrough.md` with implementation details and test proofs.
