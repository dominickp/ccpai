# ccpai

Make `prompts.json` in the same directory with this structure:
```json
[
    "homer simpson in feudal japan with, advanced swordplay",
]
```

```sh
# Install requests with pip/pip3 or use a venv or something
pip3 install requests
# Start generating
python3 main.py
```

It will choose a random prompt, generate it, and keep doing that in a loop. It reads from `prompts.json` every iteration, so you can leave it running and make changes to that file.

Check the generated `results.json` to see which prompts are getting refused.

Videos should be saved to `./out`.

Example log output:
```
INFO:root:Starting generation:
        homer simpson in feudal japan with, advanced swordplay
INFO:root:Check - (1) 0% - Ahead of you are 58 people，Expected waiting time 5 minutes
INFO:root:Check - (1) 4% - Generating, AI will continue to generate after exiting
INFO:root:Check - (1) 14% - Generating, AI will continue to generate after exiting
INFO:root:Check - (1) 24% - Generating, AI will continue to generate after exiting
INFO:root:Check - (1) 34% - Generating, AI will continue to generate after exiting
INFO:root:Check - (1) 44% - Generating, AI will continue to generate after exiting
INFO:root:Check - (1) 55% - Generating, AI will continue to generate after exiting
INFO:root:Check - (1) 65% - Generating, AI will continue to generate after exiting
INFO:root:Check - (1) 75% - Generating, AI will continue to generate after exiting
INFO:root:Check - (1) 85% - Generating, AI will continue to generate after exiting
INFO:root:Check - (1) 95% - Generating, AI will continue to generate after exiting
INFO:root:Check - (2) 100% - 
INFO:root:Video URL: https://redacted.mp4
INFO:root:Video downloaded: homer_simpson_in_feudal_japan_with_advanced_swordplay_291056142990704643
INFO:root:Sleeping 30 seconds before next generation... (1 succeeded, 0 failed)

INFO:root:Starting generation:
        homer simpson in feudal japan with, advanced swordplay
INFO:root:Check - (1) 0% - Ahead of you are 92 people，Expected waiting time 5 minutes
INFO:root:Check - (1) 3% - Generating, AI will continue to generate after exiting
INFO:root:Check - (1) 13% - Generating, AI will continue to generate after exiting
INFO:root:Check - (1) 23% - Generating, AI will continue to generate after exiting
INFO:root:Check - (1) 33% - Generating, AI will continue to generate after exiting
INFO:root:Check - (1) 43% - Generating, AI will continue to generate after exiting
INFO:root:Check - (1) 53% - Generating, AI will continue to generate after exiting
INFO:root:Check - (1) 63% - Generating, AI will continue to generate after exiting
INFO:root:Check - (1) 73% - Generating, AI will continue to generate after exiting
INFO:root:Check - (1) 83% - Generating, AI will continue to generate after exiting
INFO:root:Check - (1) 94% - Generating, AI will continue to generate after exiting
INFO:root:Check - (2) 100% - 
INFO:root:Video URL: https://redacted.mp4
INFO:root:Video downloaded: homer_simpson_in_feudal_japan_with_advanced_swordplay_291057702843944966
INFO:root:Sleeping 30 seconds before next generation... (2 succeeded, 0 failed)
```

Video output:
```sh
$ ls ./out | grep homer
homer_simpson_in_feudal_japan_with_advanced_swordplay_291056142990704643.mp4
homer_simpson_in_feudal_japan_with_advanced_swordplay_291057702843944966.mp4
```

Example results.json:
```json
{
    "homer simpson in feudal japan with, advanced swordplay": {
        "generate_success": 2,
        "prompt_refused": 0,
        "check_failed": 0
    }
}
```
