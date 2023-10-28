A fishing bot for World of Warcraft Classic.

## Disclaimer

This is intended for learning purposes only. I don't condone the use of botting in official World of Warcraft servers. By using this bot, you might get your account banned.

## How it works

The script attempts to find a close occurrence of blue and red - the main colors of the bobber's model - and then click on it when there's a splash of water.

DEBUG mode is `True` by default, allowing one to see the box within which the script is looking for the bobber.

## Development

Create a virtual environment:

```sh
$ pyenv virtualenv 3.12 wowtofisher  # or your virtual environment tool of choice
$ pyenv activate wowtofisher
```

Install the dependencies:

```sh
$ pip install -r requirements.txt
```

## Running

Stand in front of a body of water, equip the fishing rod and change to a first person view. Then run the script with:

```sh
$ python main.py
```

The default behaviour is to track the bobber inside a box at the center of the WoW window. With the DEBUG mode, a window will pop up showing you the tracked area. You can use this view to adjust your camera's position to ensure the bobber falls within the tracked area.

You can adjust the `SENSITIVITY` setting if the bobber isn't being found consistently.

## Future work

Currently, the bot *mostly* works. The tracking works better in some areas of the game world than others. Further tweaking of the color matching behaviour is still needed to ensure a higher percentage of success.

I'd also like to make the behaviour of the bot more organic - so as not to trigger bot detection measures.
