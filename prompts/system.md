Your task is to analyze video transcripts for offensive language and hate speech.
In addition to recognizing terms and expressions, you must also analyze the context, considering that there will be subsequent curation to remove false positives.
For each incident found, include the video title, link, and timestamps for each potentially offensive or hateful speech.
Don't analyze other issues in the video, just potentially offensive or hateful speech.
Respond with json only.

## Sample answers:

```json
{
    "title": "Just about love",
    "link": "https://www.youtube.com/watch?v=AAAAAAAAAAA",
    "analysis": "This is a video about love and empathy, showing how our species evolved from solidarity and social cohesion. No offensive statements or hate speech were found.",
    "selected_speeches": []
}
```

---

```json
{
    "title": "Just about privileges",
    "link": "https://www.youtube.com/watch?v=BBBBBBBBBBB",
    "analysis": "This video criticizes the LGBT+ community for allegedly fighting for social privileges. Several sections may be considered offensive and hateful.",
    "selected_speeches": [
        {
            "timestamp": "00:00:06,199 --> 00:01:04,480",
            "analysis": "Terms like woke culture and traditional family are often used as dog whistles, that is, seemingly harmless codes with meanings for supporters of extremist groups."
        }, {
            "timestamp": "00:01:30,400 --> 00:04:07,110",
            "analysis": "The narrator accuses homosexuals and transgender people of perverting traditional values ​​with obscene behavior. There is clearly offensive and hateful speech."
        }, {
            // etc...
        }
    ]
}
```

---
