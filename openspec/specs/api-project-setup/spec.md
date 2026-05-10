# api-project-setup Specification

## Purpose
TBD - created by archiving change api-mocked-server. Update Purpose after archive.
## Requirements
### Requirement: requirements.in dependency file
The project SHALL use `requirements.in` to declare Python dependencies with `~=` version specifiers.

#### Scenario: Dependencies declared
- **WHEN** a developer inspects `requirements.in`
- **THEN** it SHALL list Flask, flask-sock, and pydantic with `~=` version pinning

#### Scenario: Install dependencies
- **WHEN** a developer runs `pip install -r requirements.in`
- **THEN** all required packages SHALL be installed in the virtual environment

### Requirement: README dependency install instructions
The README SHALL include instructions for installing dependencies from `requirements.in`.

#### Scenario: README contains install steps
- **WHEN** a developer reads the README
- **THEN** it SHALL contain a section explaining how to install dependencies using `pip install -r requirements.in`

### Requirement: README updated run commands
The README SHALL reflect the renamed `api/` module in all run commands.

#### Scenario: Run command uses api module
- **WHEN** a developer reads the README Usage section
- **THEN** the run command SHALL be `python -m api.main` instead of `python -m backend.main`

#### Scenario: Boardless mode command uses api module
- **WHEN** a developer reads the README Development section
- **THEN** the boardless mode command SHALL be `BOARDLESS_MODE=true python -m api.main`

### Requirement: NFC demo preserved as exp module
The existing NFC demo from `backend/main.py` SHALL be moved to `exp/nfc_test.py`.

#### Scenario: Run NFC demo from new location
- **WHEN** a developer runs `python -m exp.nfc_test`
- **THEN** the NFC read/write demo menu SHALL work as before

### Requirement: README documents NFC test location
The README SHALL document the new location of the NFC demo.

#### Scenario: README lists nfc_test command
- **WHEN** a developer reads the README
- **THEN** it SHALL include `python -m exp.nfc_test` as the command to run the NFC demo

