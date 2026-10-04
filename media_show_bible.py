"""Quantum Forge original animation show briefs and production prompts.

These are creative briefs for owned-IP development. Visual references may be used only
to study broad qualities such as color, composition, lighting, pacing and rendering.
Do not copy protected characters, exact artwork, logos, names, costumes or living
artists' distinctive styles.
"""

SHOW_PROMPTS = {
    "Paradise Fall": {
        "format": "original science-fantasy animated series, shorts, trailers and mini-movie concepts",
        "core": """Humanity discovers a distant planet and transforms it into a paradise. Generations
later, ancient godlike beings who originated there return and declare humanity's
settlement an invasion. Humans adapted to the planet have developed extraordinary
abilities and defend the home they built, while the ancient species believes it is
reclaiming its world. The story explores survival, identity, ownership, technology,
adaptation and whether either side truly understands the planet's history.""",
        "characters": [
            "Human defenders: generations of settlers adapted to the planet, some with extraordinary abilities.",
            "Ancient godlike species: powerful original inhabitants returning after an unexplained absence.",
            "Human scientists and engineers: builders of the paradise cities, spacecraft and survival technology.",
            "Alien creatures: native lifeforms ranging from peaceful ecosystems to dangerous predators."
        ],
        "technology": """Original futuristic technology including advanced protective suits, anti-gravity
vehicles, flying spacecraft, hoverboards, planetary engineering systems and defensive
technology. Keep the technology fictional and cinematic rather than providing real-world
weapon construction instructions.""",
        "world": """A massive alien world with breathtaking paradise regions, enormous futuristic human
cities, ancient ruins, strange ecosystems, floating infrastructure and dangerous
frontier zones. Contrast beautiful civilization with mysterious remnants of the
ancient species.""",
        "visual_prompt": """Original cinematic science-fantasy animation: enormous alien landscapes, luminous
ecosystems, futuristic paradise cities, floating architecture, sleek original spacecraft,
anti-gravity boards, advanced suits, ancient colossal ruins, mysterious godlike beings,
dramatic skies, spectacular scale, emotional character moments and dynamic original
action sequences."""
    },
    "Juno the Jumping Dolphin": {
        "format": "children's animated series and shorts",
        "core": """Juno is a funny, energetic jumping dolphin who leads an underwater friend group.
Andy is a curious human boy Juno meets at the beach. Juno gives Andy an original
underwater helmet and compact jet pack so Andy can safely explore underwater.
The story can move between the ocean, Andy's school and Andy's loving, funny family home.""",
        "characters": [
            "Juno: energetic dolphin, playful, curious, joke-driven leader.",
            "Big Blue: enormous whale with a deep voice, calm and laid-back even during chaos.",
            "Clammy: a talking clam whose terrible jokes trigger a recurring group 'wha-wha-wha' reaction and a comedic drum sting.",
            "Crabby: expressive crab with a funny temper and practical problem-solving.",
            "Selly: curious seahorse who loves patterns, questions and discovery.",
            "Octo: eight-armed octopus whose abilities create visual comedy and clever solutions.",
            "The King: underwater ruler who introduces challenges, mysteries and adventures.",
            "Andy: human boy who connects the underwater world to school, family life and everyday lessons."
        ],
        "learning": """Every episode must contain real learning woven into the plot: reading, counting,
vocabulary, problem-solving, life skills and accurate facts about marine animals,
habitats, ecosystems and ocean science. Learning should help solve the story problem,
not feel like a lecture.""",
        "visual_prompt": """Original high-end family animation: colorful cinematic underwater world,
expressive original animal characters, appealing silhouettes, rich facial animation,
warm comedy, beautiful coral environments, underwater kingdoms, dynamic bubbles and
light rays, polished feature-animation quality, family-friendly, memorable character
designs, cinematic composition, original IP."""
    },
    "Bloodline": {
        "format": "original cyberpunk anime series, shorts, trailers and mini-movie concepts",
        "canonical_character": "Diamond Infinity — use bloodline_character_bible.py as the locked continuity reference.",
        "core": """Bloodline follows Diamond Infinity, a college student who wants to become a scientist
like his late father. His father created an experimental serum intended to help
Diamond's sick sister, Eternity Infinity, but a powerful government-linked weapons
corporation called Murder Co. raided the laboratory, murdered his father and tried to
take the research. Diamond studies science while refining the research and inventing
advanced technology of his own.""",
        "characters": [
            "Diamond Infinity: brilliant college student, scientist-in-training, inventor and reluctant hero.",
            "Eternity Infinity: Diamond's sister, whose illness gives the original serum research its emotional purpose.",
            "Diamond's mother: loving, resilient and quietly grieving while protecting her family.",
            "Murder Co.: fictional corporate antagonist developing secret weapons and an unstable version of the serum.",
            "Murder Co. enhanced soldiers: dangerous fictional figures transformed by an imperfect serum, supported by advanced weapons and machines."
        ],
        "technology": """Diamond develops an original flying armored suit, compact propulsion systems,
advanced gadgets and a leg-deployed energy sword. When activated, the fictional
blade produces a dramatic wide-area flame/energy effect for stylized animation.
Keep all technology fictional and cinematic rather than presenting real weapon-building
instructions.""",
        "world": """One enormous futuristic city is the main backdrop. Diamond's school and home are
in cleaner, beautiful districts with advanced architecture. Other areas contain
towering skyscrapers, neon signs, dark alleys, industrial zones and rougher
neighborhoods. The city should feel dense, layered and futuristic with a cyberpunk
atmosphere, while remaining an original setting.""",
        "visual_prompt": """Original cyberpunk anime-inspired visual direction: dramatic Japanese animation
energy, expressive original characters, huge futuristic megacity, neon signs glowing
through dark rain-soaked alleys, towering skyscrapers, layered transit systems,
industrial/slum contrasts, beautiful advanced university and residential districts,
cinematic night lighting, dynamic aerial movement, futuristic armor, original flying
vehicles, intense stylized action, rich backgrounds, high-detail animation, original
character and costume designs."""
    }
}

def production_directive(show_name: str) -> str:
    brief = SHOW_PROMPTS[show_name]
    return (
        f"CREATE ORIGINAL CONTENT FOR: {show_name}\n"
        f"FORMAT: {brief['format']}\n"
        f"CORE: {brief['core']}\n"
        + (diamond_directive() if show_name == "Bloodline" else "")
        "RULE: Use StarryAI outputs or other references only to study broad visual "
        "qualities. Rebuild the characters, environments and compositions as original "
        "Quantum Forge IP. Do not reproduce protected characters, logos, exact scenes, "
        "or another creator's artwork.\n"
        "WORKFLOW: concept -> character continuity -> script -> storyboard -> visual "
        "prompt -> generated shots -> edit -> voice/music -> quality check -> YouTube "
        "short/episode/mini-movie package.\n"
    )

def youtube_content_tasks() -> list[str]:
    return [
        "Create short proof-of-concept videos before investing in longer episodes.",
        "Create original trailers, character introductions and scene teasers.",
        "Keep a continuity bible so characters look and behave consistently.",
        "Generate titles, thumbnails and descriptions optimized for discovery without deception.",
        "Track views, retention, comments and subscriber growth and use those results to improve later episodes.",
        "Never claim a video generated revenue until the payment is independently verified.",
    ]
