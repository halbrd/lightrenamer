# lightrenamer
An absolute barebones thetvdb renamer.

Requires Python 3.6+. If you only have an earlier version, you can probably convert the script pretty quickly and easily by replacing the f-strings.

## Usage

### Generate credentials the first time
```
python3 lightrenamer.py --api-key the_api_key_that_you_got_from_https://www.thetvdb.com/member/api
```

### Invoking
To rename files like this:
```
Avatar The Last Airbender S01E01 - The Boy in the Iceberg.mkv
Avatar The Last Airbender S1E12.mkv
Avatar The Last Airbender s01e13.mkv
Avatar The Last Airbender 02x11.mkv
Avatar The Last Airbender 2x12 - .mkv
Avatar The Last Airbender 2X13 - .mkv
```

Invoke:
```
python3 lightrenamer.py Avatar
```

Which will rename them to:
```
Avatar- The Last Airbender S01E01 - The Boy in the Iceberg.mkv
Avatar- The Last Airbender S01E12 - The Storm.mkv
Avatar- The Last Airbender S01E13 - The Blue Spirit.mkv
Avatar- The Last Airbender S02E11 - The Desert.mkv
Avatar- The Last Airbender S02E12 - The Serpent's Pass.mkv
Avatar- The Last Airbender S02E13 - The Drill.mkv
```

## Troubleshooting
If the script can't use DVD order for some reason, you can use the `--aired-order` switch to try using the aired order instead.

```
python3 lightrenamer.py --aired-order Avatar
```

## Customization
There aren't many options baked into the script by default, as the design philosophy is to be lightweight. The script is so short and simple that changes to its behaviour are better left to end user modifications of the script rather than being built in, tested, and supported.
