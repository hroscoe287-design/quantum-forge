"""Bloodline Episode 1 production package.

Original dark supernatural battle-shonen production blueprint for Quantum Forge agents.
This is a production specification, not a finished video file.
"""

from bloodline_character_bible import diamond_directive

TITLE = "BLOODLINE — Episode 1: The Awakening"
LOGLINE = (
    "On the night Diamond discovers a hidden message from his dead scientist father, "
    "a violent supernatural attack forces the young inventor to awaken a power his father "
    "spent his life trying to control."
)

TONE = "dark, emotional, high-energy supernatural action with mystery, humor under pressure, and cinematic cliffhangers"

EPISODE = {
    "runtime_target": "8-12 minutes",
    "opening_hook": (
        "Cold open: a ruined underground laboratory, emergency lights flashing, a young man's "
        "voice warning that the Bloodline must never be awakened. Cut to Diamond waking from the dream."
    ),
    "scenes": [
        {
            "id": 1,
            "title": "The Dream",
            "purpose": "Establish mystery and the father's warning.",
            "beats": [
                "Diamond sees fragments of his father's laboratory collapsing.",
                "His father reaches toward the camera and says the serum was never the real experiment.",
                "A shadowed supernatural figure appears behind him.",
                "Diamond wakes with the blue pendant burning cold against his chest."
            ],
        },
        {
            "id": 2,
            "title": "Campus Pressure",
            "purpose": "Show Diamond's normal life and personality.",
            "beats": [
                "Diamond works on a small scientific prototype between classes.",
                "He is brilliant but distracted by unanswered questions about his father's death.",
                "A strange pulse from the pendant disrupts his prototype.",
                "He notices a symbol matching one from his father's old research notes."
            ],
        },
        {
            "id": 3,
            "title": "The Message",
            "purpose": "Launch the central mystery.",
            "beats": [
                "Diamond discovers a hidden recording encoded inside an old research file.",
                "His father warns him not to trust anyone searching for the Bloodline.",
                "The recording cuts out as the campus lights fail.",
                "Diamond realizes someone else has accessed the file."
            ],
        },
        {
            "id": 4,
            "title": "The Attack",
            "purpose": "Introduce supernatural danger.",
            "beats": [
                "A hostile supernatural entity enters the campus grounds.",
                "Diamond protects another student instead of escaping.",
                "His scientific instincts let him recognize patterns in the entity's movement.",
                "He is overwhelmed and badly injured."
            ],
        },
        {
            "id": 5,
            "title": "Bloodline Awakening",
            "purpose": "Deliver the first major power moment.",
            "beats": [
                "Diamond's pendant cracks and releases blue energy.",
                "His eyes flash electric blue and the environment reacts to his pressure-like aura.",
                "His senses accelerate and he begins reading the attacker's movement.",
                "Diamond lands his first powered counterattack.",
                "The power surge nearly overwhelms his body."
            ],
        },
        {
            "id": 6,
            "title": "The Survivor",
            "purpose": "End with mystery and a sequel hook.",
            "beats": [
                "The entity retreats after sensing Diamond's awakening.",
                "Diamond discovers a strange mark left behind at the scene.",
                "A distant observer reports that the Bloodline has awakened.",
                "Diamond looks at his father's pendant and says he is going to find the truth.",
                "Final shot: an unseen faction prepares for Diamond's next awakening."
            ],
        },
    ],
    "ending_hook": "A hidden organization now knows Diamond is alive and awakened.",
}

VISUAL_DIRECTION = {
    "character": diamond_directive(),
    "style": (
        "original premium dark supernatural battle-shonen anime; cinematic lighting; dynamic "
        "camera angles; expressive faces; powerful silhouettes; dramatic environmental effects; "
        "consistent character continuity; no copyrighted characters, logos, costumes, weapons, "
        "or copied scenes"
    ),
    "action": (
        "fast readable choreography, impact frames, speed lines used sparingly, debris, controlled "
        "energy effects, tactical movement, clear cause-and-effect, emotional reactions"
    ),
}

AUDIO_DIRECTION = {
    "music": "original dark orchestral/electronic score with restrained tension, escalating percussion during combat, and a powerful original awakening motif",
    "voices": "distinct original voices for Diamond, his father, supporting students, and the unseen faction",
    "effects": "campus ambience, laboratory electronics, electrical pulses, impacts, supernatural pressure, energy surges, debris",
}

YOUTUBE_PACKAGE = {
    "title": TITLE,
    "description": (
        "Diamond thought his father's death was the end of the mystery. Then a hidden message, "
        "a supernatural attack, and a power buried inside his bloodline change everything. "
        "BLOODLINE begins here."
    ),
    "thumbnail": (
        "Diamond in the foreground with electric-blue eyes and blue energy erupting around him, "
        "dark ruined laboratory behind him, mysterious silhouette in the background, bold original "
        "BLOODLINE title treatment, cinematic anime composition."
    ),
}

AGENT_HANDOFF = [
    "Showrunner: approve pacing, tone and episode arc.",
    "Screenwriter: expand scenes into dialogue and screenplay.",
    "StoryboardAgent: turn every beat into shot-level boards.",
    "CharacterContinuityAgent: enforce Diamond bible across every shot.",
    "VisualPromptAgent: create original image/video prompts.",
    "VoiceMusicAgent: create dialogue, narration and original audio direction.",
    "ThumbnailAgent: produce multiple original thumbnail concepts.",
    "MediaQualityAgent: reject continuity, originality or quality failures before publishing.",
]

def production_package():
    return {
        "title": TITLE,
        "logline": LOGLINE,
        "tone": TONE,
        "episode": EPISODE,
        "visual_direction": VISUAL_DIRECTION,
        "audio_direction": AUDIO_DIRECTION,
        "youtube_package": YOUTUBE_PACKAGE,
        "agent_handoff": AGENT_HANDOFF,
    }
