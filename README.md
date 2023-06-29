## LuxmedHunter

Simple tool to notify about available slot in LUX MED medical care service using Pushbullet notifications.
___
My twist of Luxmed appointments notifier, inspiration taken from:  
https://github.com/pawliczka/LuxmedSniper  
https://github.com/m-grzesiak/yalma

Mainly done to accomplish the same things as their projects but to train my skills in more Pythonic & OOP ways.  
And to use dataframes. I love dataframes.
___
### Ways to run:
- Raw python
- Docker
- Docker-compose
___

### Config
You shall use polish letters/alphabet for names, capitalization doesn't matter. The name of service, city,
doctor should be a string, exactly as they are visible in the phone app. To help, the bot saves list of
cities and services to text files on the first run. `doctor_name` and `clinic_name` are optional - 
to dial in the search (they can be left empty).

### Installation

#### Python requirements:

- Python 3.10.0 or newer
- Poetry (superior virtualenv)
- Pushbullet token (phone app, browser extension, what you prefer, you need an account)

If you don't have poetry, you can create poetry venv base on `.lock` and `.toml` with your IDE, or going the raw
method: `pip install poetry`, within the project directory run `poetry install`, activate the environment with
`poetry shell`.
___
To use it, create `.env` file based on the `.env.template` with your details and run the `luxmed_runner`.

### Docker requirements:

- Docker / Docker-compose

As this can be run as docker container, image of this repo is automatically created with new pushes and uploaded to
GHCR, please refer to my packages:
https://github.com/Kalindro/luxmedhunter/pkgs/container/luxmedhunter  
The environmental variables should be provided, the same variables that shall be passed to the `.env` file.
There is also `docker-compose` available, for sake of Portainer easier compatibility it looks for `stacks.env` file.
___
Please be advised that running too many queries against LuxMed API may result in locking your LuxMed account.
Breaching the "fair use policy" for the first time locks the account temporarily for 1 day. Breaching it
again locks it indefinitely and manual intervention with "Patient Portal Support" is required to unlock it.
There are safeguards in the script, nonetheless a friendly reminder.

