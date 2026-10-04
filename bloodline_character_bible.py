""""Bloodline character continuity bible.

Diamond is the locked protagonist design for Quantum Forge's original Bloodline IP.
The series is an original dark supernatural battle-shonen: explosive hand-to-hand and
weapon combat, spiritual energy, rival factions, transformations, mystery and emotional stakes.
Use this as the canonical reference for every script, storyboard, image prompt, video prompt,
thumbnail and episode. It may capture broad genre energy, but must not copy Bleach or any other
protected character, costume, weapon, lore, terminology, scene, or artwork.
"""

DIAMOND = {
    "name": "Diamond Infinity",
    "role": "college student, scientist-in-training, inventor and reluctant supernatural warrior",
    "age": "18-22",
    "identity": "young Black college student",
    "core_personality": "brilliant, stubborn, funny under pressure, protective of others, emotionally guarded, and driven to understand his father's work",
    "face": "handsome youthful face with strong brows, expressive eyes, a sharp determined gaze and a subtle confident smirk when challenged",
    "hair": "short dense black textured curls with clean shaved/etched side detailing; slightly wild during combat",
    "eyes": "deep brown at rest; flash electric blue when his bloodline power rises",
    "build": "lean athletic college build; develops a powerful fighter's physique as his bloodline awakens",
    "casual_outfit": "black fitted streetwear jacket, dark shirt, tapered cargo pants, high-top sneakers, blue accents",
    "battle_outfit": "original black combat jacket with reinforced panels, open collar, flexible pants and boots; blue energy seams appear only after activation",
    "signature_item": "small blue diamond-shaped pendant on a chain, connected to the mystery of his father's serum",
    "combat_style": "fast close-quarters combat combining athletic footwork, evasive movement, brutal counters and controlled blue energy; later evolves into a distinctive supernatural weapon style",
    "power_identity": "Bloodline energy: a rare bio-spiritual force created by the interaction between his father's serum research and Diamond's inherited biology",
    "palette": ["black", "deep navy", "electric blue", "white", "silver", "controlled violet-blue energy accents"],
    "normal_state": "calm, intelligent, observant college student who would rather solve a problem than fight",
    "awakening_state": "breathing slows, eyes ignite electric blue, a pressure-like aura bends dust and loose objects, and faint blue energy markings appear across his arms",
    "battle_state": "fast, aggressive and highly tactical; blue energy reinforces strikes, movement and defense without making him instantly unbeatable",
    "first_transformation": "an incomplete Bloodline awakening that dramatically boosts speed, strength, perception and energy control while creating a dangerous physical cost",
    "long_term_evolution": "Diamond gradually learns that his father's serum did not simply create super soldiers; it interacts with a hidden supernatural force and may have been designed for a much larger war",
    "continuity_rules": [
        "Keep Diamond's face, skin tone, age, hairstyle and proportions consistent across shots and episodes.",
        "Keep the blue diamond pendant as his recurring signature item unless a scene explicitly removes it.",
        "Keep his everyday identity grounded: he is still a college student and scientist-in-training between battles.",
        "His powers must develop in stages; avoid giving him unlimited abilities at the beginning.",
        "Combat should feel fast, dangerous and cinematic, with clear impact, movement and tactical choices.",
        "The supernatural system must remain original: no copied Soul Reaper, Hollow, Bankai, Zanpakuto, Bleach terminology or equivalent one-to-one concepts.",
        "Weapons, factions, transformations, monsters and power names must be newly invented for Bloodline.",
        "Enhanced forms change power, aura and physique but always remain unmistakably Diamond.",
        "Do not redesign Diamond between episodes without an explicit story reason.",
        "Do not use copyrighted characters, logos, exact costumes or another creator's artwork as a template."
    ],
    "visual_prompt": (
        "Original premium dark supernatural battle-shonen anime protagonist, Diamond Infinity, "
        "young Black college student and scientist-in-training, short dense black textured curls "
        "with subtle shaved side detailing, deep brown eyes flashing electric blue during power "
        "activation, lean athletic fighter build, black fitted combat streetwear with navy and "
        "silver details, small blue diamond pendant, cinematic night city, dramatic perspective, "
        "strong silhouette, expressive face, dynamic motion, supernatural blue pressure aura, "
        "high-detail original character design, sharp action composition, emotional intensity. "
        "Avoid resemblance to existing anime characters, costumes, weapons or logos."
    ),
}

def diamond_directive() -> str:
    d = DIAMOND
    rules = "\n".join(f"- {x}" for x in d["continuity_rules"])
    return (
        "CANONICAL CHARACTER: Diamond Infinity\n"
        f"AGE: {d['age']}\n"
        f"ROLE: {d['role']}\n"
        f"PERSONALITY: {d['core_personality']}\n"
        f"POWER IDENTITY: {d['power_identity']}\n"
        f"COMBAT STYLE: {d['combat_style']}\n"
        f"VISUAL: {d['visual_prompt']}\n"
        "CONTINUITY RULES:\n" + rules + "\n"
    )
