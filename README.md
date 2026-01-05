# Formidable-Grid

## Project overview

This project performs quasi‑static time‑series (QSTS) simulations of a distribution network populated with grid‑forming inverters (GFMIs). Simulations support both islanded and grid‑connected operation and use OpenDSS to model electrical behavior and controller interactions.

### Key features

- QSTS simulations for long‑term, time‑stepped studies  
- Multiple GFMIs with configurable control and placement  
- Support for islanded and grid‑connected scenarios  
- Exportable time series of voltages, currents, powers and frequencies  
- Built on OpenDSS for component-level electrical modelling

### Test network data

Simulations are driven by example network files derived from the IEEE 123‑bus distribution dataset available on OpenEI: https://openei.org/wiki/OEDI_SI/Data/IEEE_123-bus_Distribution_Network_Data

## Init project

1. You need to install `make`: `sudo apt update && sudo apt install make`
2. Then, run `make install-all` or `make venv-activate` if everything is already installed.
3. If you delete your `.venv`, you can run `make install-all` to install everything from beginning.

### Start the project

Use docker services and native containers for development:
```sh
make start # it opens two pane (servers and development backend)
```

### Stop and Remove docker services

Stop and remove docker services with following commands:
```sh
make stop # it stops all services
make down # it removes all existing services 
```

### Generate new power profiles

The power profile is generated from SQL data recording measurements from HEIG-VD. Alternatively, you can use datasets in Parquet format located in the `data/inputs` folder. To run the desired endpoints, a `.secrets.toml` file must be placed in the formidable folder on the Switch drive to access the private MySQL server. This file should include the following variable:

```sh
POWER_PROFILE_SCHOOL_SQL_URL = "mysql+pymysql://db_user:db_pass@host:port/db_name"
```

## Main contributors

Mohammad Rayati (2025-Present) 

   <img src="https://storage.googleapis.com/b2match-as-1/Nc8fdSxuHaruZFc1kGLr4uic" width="200">

## Funding projects

<img src="https://www.myblueplanet.ch/wp-content/uploads/2024/05/25.03.15-Logo-Schweizer-Bundesamt-fuer-Energie-scaled.jpg" width="200">

Research Programme Grids
Call 2023
