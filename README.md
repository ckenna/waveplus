# Introduction

A simple set of scripts to discover an Airthings [Wave Plus](https://www.airthings.com/wave-plus) device, fetch its metrics over Bluetooth, and save the results in a [Graphite](https://graphiteapp.org/) database. From there, you can graph it with something like Grafana.

It can create dashboards like the following:

![Grafana screenshot](/grafana.png?raw=true "Grafana screenshot")

# Dependencies

Install these dependencies on a Raspberry Pi running Ubuntu:

    python3 pipenv bluetooth bluez

There could be more dependencies, but I installed them so long ago I forget any additional.

# Setup the Python `pipenv` environment

Create the `pipenv` environment and install the dependencies. Check out the `pipenv` documentation for this. This is usually just a `pipenv install` command.

# Discover your Airthings 

Next, find your device. There is a simple find script that scans for 5 seconds and prints out any MACs for Airthings devices it finds, filtering out all the Bluetooth junk from the environment (my neighbors have a bunch of Schlage locks and phones broadcasting).

To run the find script, you need root (preserving the environment for Pipenv to function):

    sudo -E pipenv run python3 find.py

Expected output (ignore the logger info at the start of the line):

    INFO:root:Found a potential Airthings with MAC address: 58:93:d8:ab:cd:ef

# Test the collection script

Finally, you can take your MAC and test that everything is working. The help on the collection script is:

    pipenv run python3 ./collect.py --help
    
    Usage: collect.py [OPTIONS] MAC GRAPHITE_HOST GRAPHITE_PREFIX
    
    Options:
      --log-level [critical|error|warning|info|debug]
                                      Log level.
      --graphite-port INTEGER         Port for Graphite.
      --graphite-dryrun / --no-graphite-dryrun
                                      Do not actually send to Graphite.
      --help                          Show this message and exit.


To execute a test run without actually sending data to Graphite, you can use the dryrun flag and any Graphite endpoint and prefix. That looks like this:

    pipenv run python3 ./collect.py --graphite-dryrun 58:93:d8:ab:cd:ef 127.0.0.1 my.sample.prefix
    
    WARNING:__main__:Dry-run: Not sending humidity=58.5
    WARNING:__main__:Dry-run: Not sending light=74
    WARNING:__main__:Dry-run: Not sending accel=0
    WARNING:__main__:Dry-run: Not sending radon_short_term_average=5
    WARNING:__main__:Dry-run: Not sending radon_long_term_average=12
    WARNING:__main__:Dry-run: Not sending temperature=19.98
    WARNING:__main__:Dry-run: Not sending pressure=1001.44
    WARNING:__main__:Dry-run: Not sending carbon_dioxide_level=465.0
    WARNING:__main__:Dry-run: Not sending voc_level=67.0


# Set up a shell script and cronjob to run the script.

In a real system, you'd create a cronjob to periodically collect your data. I like to use a shell script to make sure I get the `pipenv` invocation correct:

A sample shell script is included as `collect.sample.sh`. Edit the variables for `MAC`, `GRAPHITE_HOST`, and `PREFIX`.

Create a cronjob that looks like this with the path to your `collect.sh` script. Make sure it is executable.

    */5 * * * * /home/ubuntu/src/waveplus/collect.sh


