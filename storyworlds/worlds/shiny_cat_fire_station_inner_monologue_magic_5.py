#!/usr/bin/env python3
"""A mystery-leaning magical storyworld set inside a fire station.

Seed:
    Words: shiny cat
    Setting: fire station
    Features: Inner Monologue, Magic
    Style: Mystery

Internal source tale:
    A child waits in a quiet fire station after rain and notices a shiny cat
    with unmistakable magic in its fur. Strange clues begin to appear around an
    old station relic, and the child's inner monologue turns the hush of the
    building into a mystery. With a gentle adult helper and the cat's glowing
    guidance, the child traces the clue to a small physical problem, fixes it,
    and ends the night with a calmer heart and a fire station that looks
    visibly restored.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample


@dataclass(frozen=True)
class StationSpot:
    key: str
    label: str
    scene: str
    ending_image: str
    supports: tuple[str, ...]


@dataclass(frozen=True)
class CatForm:
    key: str
    label: str
    coat: str
    magic: str
    ending_pose: str
    supports: tuple[str, ...]


@dataclass(frozen=True)
class Mystery:
    key: str
    kind: str
    label: str
    source: str
    omen: str
    thought: str
    inspect: str
    reveal: str
    risk: str
    ending_change: str


@dataclass(frozen=True)
class Remedy:
    key: str
    kind: str
    label: str
    helper_action: str
    action: str
    result: str
    image: str


@dataclass(frozen=True)
class Relic:
    key: str
    title: str
    display: str
    legend: str
    lesson: str
    echoes: tuple[str, ...]


@dataclass
class StoryParams:
    spot: str
    cat: str
    mystery: str
    remedy: str
    relic: str
    hero: str
    gender: str
    helper: str
    trait: str
    seed: int | None = None


@dataclass
class Entity:
    key: str
    kind: str
    label: str
    location: str
    tags: dict[str, str] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def set_meter(self, name: str, value: float) -> None:
        self.meters[name] = round(value, 2)

    def add_meter(self, name: str, amount: float) -> None:
        self.meters[name] = round(self.meters.get(name, 0.0) + amount, 2)

    def add_meme(self, name: str, amount: float) -> None:
        self.memes[name] = round(self.memes.get(name, 0.0) + amount, 2)


@dataclass
class Event:
    key: str
    detail: str
    effect: str = ""


@dataclass
class World:
    params: StoryParams
    spot: StationSpot
    cat: CatForm
    mystery: Mystery
    remedy: Remedy
    relic: Relic
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    facts: dict[str, str] = field(default_factory=dict)
    fired: list[str] = field(default_factory=list)

    def event(self, key: str, detail: str, effect: str = "") -> None:
        self.history.append(Event(key=key, detail=detail, effect=effect))
        self.fired.append(key)

    def trace(self) -> str:
        rows = ["--- world model state ---", f"params={self.params}"]
        for key, ent in self.entities.items():
            rows.append(
                f"{key}: kind={ent.kind} label={ent.label} location={ent.location} "
                f"tags={dict(sorted(ent.tags.items()))} "
                f"meters={dict(sorted(ent.meters.items()))} "
                f"memes={dict(sorted(ent.memes.items()))}"
            )
        rows.append(f"facts={json.dumps(self.facts, sort_keys=True)}")
        rows.append(f"fired={self.fired}")
        rows.append("history:")
        for item in self.history:
            rows.append(
                f"  {item.key}: {item.detail}" + (f" -> {item.effect}" if item.effect else "")
            )
        return "\n".join(rows)


SPOTS = {
    "hose_bay": StationSpot(
        key="hose_bay",
        label="the hose bay",
        scene="parked engines gleamed in red rows, wet boots dried by the wall, and the coiled hoses looked like sleeping serpents",
        ending_image="the hose bay shone with the clean, brave stillness a fire station keeps after a worry has been understood",
        supports=("pawtrail", "bell_echo"),
    ),
    "gear_room": StationSpot(
        key="gear_room",
        label="the gear room",
        scene="silver hooks held jackets shoulder to shoulder, helmet lights blinked softly, and one long bench ran beneath the lockers",
        ending_image="the gear room looked orderly again, as if every hook and helmet knew its proper place",
        supports=("pawtrail", "soot_riddle"),
    ),
    "watch_desk": StationSpot(
        key="watch_desk",
        label="the watch desk corner",
        scene="maps, radios, and pencils waited under a green lamp while the night windows reflected the station back in small dark panes",
        ending_image="the watch desk settled into a thoughtful glow, ready for work instead of whispers",
        supports=("bell_echo", "soot_riddle"),
    ),
}


CATS = {
    "brass_whiskers": CatForm(
        key="brass_whiskers",
        label="a shiny cat named Gleam",
        coat="Its fur looked smooth as polished brass, and each whisker flashed when it turned its face.",
        magic="There was real magic in the animal: when it paused, hidden edges caught light that had not been there a moment before.",
        ending_pose="The shiny cat curled on a folded jacket and blinked as if the mystery had been tucked away with its paws.",
        supports=("pawtrail", "bell_echo"),
    ),
    "moon_polish": CatForm(
        key="moon_polish",
        label="a shiny cat named Luster",
        coat="Its coat held a moon-silver gloss, bright enough to make the dark corners of the station seem full of secrets.",
        magic="Soft magic moved with the cat, because every blink sent a pale shimmer toward the clue it wanted noticed.",
        ending_pose="The shiny cat sat beneath the lamp with its tail around its paws, looking pleased that the station could rest again.",
        supports=("bell_echo", "soot_riddle"),
    ),
    "ember_paws": CatForm(
        key="ember_paws",
        label="a shiny cat named Spark",
        coat="Its paws were glossy as fresh paint, and a warm copper shine ran along its tail.",
        magic="The cat carried gentle magic; a thin gleam followed its steps and made the right hiding place easier to see.",
        ending_pose="The shiny cat stretched beside the boots and let the last little glow fade from its paws.",
        supports=("pawtrail", "soot_riddle"),
    ),
}


MYSTERIES = {
    "silver_pawtrail": Mystery(
        key="silver_pawtrail",
        kind="pawtrail",
        label="a silver pawprint trail",
        source="locker",
        omen="A line of silver pawprints appeared across the floor and stopped at a narrow locker under the hanging coats.",
        thought="If {relic_title} is telling the truth, maybe the shiny cat has come because the fire station is trying to whisper a secret to me.",
        inspect="The child crouched beside the glowing prints and saw that every mark pointed to the same stiff locker door.",
        reveal="Inside the partly stuck locker, a small safety lantern charm had slipped from its peg and was throwing light in nervous little jumps.",
        risk="the corner would keep feeling haunted, and no one would find the missing charm before the next night check",
        ending_change="the silver pawprints faded into a friendly shine on the floor",
    ),
    "lonely_bell": Mystery(
        key="lonely_bell",
        kind="bell_echo",
        label="a lonely bell note",
        source="bell",
        omen="The old station bell gave one soft ring even though no one was touching the rope.",
        thought="If the warning in {relic_title} is awake, maybe the shiny cat is telling me the fire station has forgotten something important.",
        inspect="Following the cat up the short stairs, the child noticed the rope twitch whenever a cool loop of air moved past the bell shelf.",
        reveal="A loose brass tag had begun tapping the bell in the draft, and the cat's shimmer made the tiny motion sound like a larger warning.",
        risk="the strange ringing could keep everyone uneasy and hide the simple thing that truly needed attention",
        ending_change="the bell rested without another lonely note",
    ),
    "soot_question": Mystery(
        key="soot_question",
        kind="soot_riddle",
        label="a soot-made question mark",
        source="vent",
        omen="On the glass of the old map case, a curl of soot drew itself into a question mark and then vanished.",
        thought="Maybe the story behind {relic_title} has stepped out of its frame, and the shiny cat wants me to solve the riddle before fear grows bigger than the truth.",
        inspect="The child breathed on the glass again and watched the soot bloom exactly where warm air touched one corner.",
        reveal="A cracked vent beside the map case was puffing dusty soot in one spot, and the cat's tail-light had turned that dust into a dark sign.",
        risk="the mystery would keep growing in every retelling, while the dusty vent still needed honest care",
        ending_change="the map glass stayed clear enough to show every street line",
    ),
}


REMEDIES = {
    "peg_the_charm": Remedy(
        key="peg_the_charm",
        kind="pawtrail",
        label="a re-hung lantern charm",
        helper_action="The helper held the heavy coats apart so the child could reach into the narrow space without hurrying.",
        action="hooked the wandering lantern charm back onto its peg and pushed the locker shut until the latch clicked",
        result="The corner brightened in an honest way, and the room stopped pretending to be haunted.",
        image="The little charm hung still like a star that had remembered where it belonged.",
    ),
    "quiet_the_tag": Remedy(
        key="quiet_the_tag",
        kind="bell_echo",
        label="a quieted bell tag",
        helper_action="The helper steadied the rail while the child climbed the last step and the cat watched from the bell shelf with bright, patient eyes.",
        action="wrapped the loose brass tag in soft tape and tied the bell rope neatly against the wall",
        result="The next small draft passed through the station, but the bell kept its peace.",
        image="The bell rope lay straight as a calm red ribbon against the wall.",
    ),
    "brush_the_vent": Remedy(
        key="brush_the_vent",
        kind="soot_riddle",
        label="a brushed vent cover",
        helper_action="The helper lifted the lamp over the map case while the child used both hands and moved slowly.",
        action="brushed the dusty vent clean and pressed a small filter square over the crack",
        result="No more soot curled across the glass, and the air smelled clean instead of singed.",
        image="The map case shone clear enough for every street to look brave again.",
    ),
}


RELICS = {
    "night_bell_ledger": Relic(
        key="night_bell_ledger",
        title="the Night Bell Ledger",
        display="a brass-framed page of old station notes beside the bell rope",
        legend="the ledger says the station remembers careful hands before it remembers loud voices",
        lesson="Small warnings grow kinder when someone notices them before fear begins to decorate them.",
        echoes=("pawtrail", "bell_echo"),
    ),
    "rescue_map": Relic(
        key="rescue_map",
        title="the Rescue Map of Willow Street",
        display="an old glass-covered map with penciled routes and neat circles around past calls",
        legend="the map is said to glow for the person who looks twice and guesses less",
        lesson="A mystery often shrinks when a patient person looks at the real place instead of the scariest idea.",
        echoes=("pawtrail", "soot_riddle"),
    ),
    "ember_manual": Relic(
        key="ember_manual",
        title="the Ember Manual",
        display="a thick station handbook opened to a page about checking little things before they become big worries",
        legend="the manual promises that brave hearts ask what is true before they ask what is frightening",
        lesson="Courage in a mystery is not loudness. It is the choice to keep looking until the clue becomes clear.",
        echoes=("bell_echo", "soot_riddle"),
    ),
}


HEROES = {
    "girl": ("Mina", "June", "Elsie", "Nora", "Poppy"),
    "boy": ("Eli", "Theo", "Owen", "Milo", "Jasper"),
}

HELPERS = ("captain", "dispatcher", "mechanic", "mother", "grandfather")
TRAITS = ("observant", "quiet", "careful", "steady", "curious")


def pronouns(gender: str) -> tuple[str, str, str]:
    if gender == "boy":
        return ("he", "his", "him")
    return ("she", "her", "her")


def titled(word: str) -> str:
    return word.replace("_", " ").title()


def article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def helper_display(word: str) -> str:
    if word in ("mother", "grandfather"):
        return titled(word)
    return f"the {word.replace('_', ' ')}"


def sentence_case(text: str) -> str:
    if not text:
        return text
    return text[0].upper() + text[1:]


def lower_first(text: str) -> str:
    if not text:
        return text
    return text[0].lower() + text[1:]


def valid_combo(spot: str, cat: str, mystery: str, remedy: str, relic: str) -> bool:
    if (
        spot not in SPOTS
        or cat not in CATS
        or mystery not in MYSTERIES
        or remedy not in REMEDIES
        or relic not in RELICS
    ):
        return False
    kind = MYSTERIES[mystery].kind
    return (
        kind in SPOTS[spot].supports
        and kind in CATS[cat].supports
        and kind in RELICS[relic].echoes
        and REMEDIES[remedy].kind == kind
    )


def explain_rejection(spot: str, cat: str, mystery: str, remedy: str, relic: str) -> str:
    if spot not in SPOTS:
        return f"No story: unknown fire-station spot {spot!r}."
    if cat not in CATS:
        return f"No story: unknown cat form {cat!r}."
    if mystery not in MYSTERIES:
        return f"No story: unknown mystery {mystery!r}."
    if remedy not in REMEDIES:
        return f"No story: unknown remedy {remedy!r}."
    if relic not in RELICS:
        return f"No story: unknown relic {relic!r}."
    kind = MYSTERIES[mystery].kind
    if kind not in SPOTS[spot].supports:
        return f"No story: {SPOTS[spot].label} does not naturally support {MYSTERIES[mystery].label}."
    if kind not in CATS[cat].supports:
        return f"No story: {CATS[cat].label} does not fit {MYSTERIES[mystery].label}."
    if kind not in RELICS[relic].echoes:
        return f"No story: {RELICS[relic].title} does not match the mood of {MYSTERIES[mystery].label}."
    if REMEDIES[remedy].kind != kind:
        return f"No story: {REMEDIES[remedy].label} does not solve {MYSTERIES[mystery].label}."
    return "No story: the requested fire-station mystery is not reasonable."


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    rows: list[tuple[str, str, str, str, str]] = []
    for spot in SPOTS:
        for cat in CATS:
            for mystery in MYSTERIES:
                for remedy in REMEDIES:
                    for relic in RELICS:
                        if valid_combo(spot, cat, mystery, remedy, relic):
                            rows.append((spot, cat, mystery, remedy, relic))
    return rows


def build_world(params: StoryParams) -> World:
    if not valid_combo(params.spot, params.cat, params.mystery, params.remedy, params.relic):
        raise StoryError(
            explain_rejection(params.spot, params.cat, params.mystery, params.remedy, params.relic)
        )

    world = World(
        params=params,
        spot=SPOTS[params.spot],
        cat=CATS[params.cat],
        mystery=MYSTERIES[params.mystery],
        remedy=REMEDIES[params.remedy],
        relic=RELICS[params.relic],
    )
    place = f"{world.spot.label} of the fire station"
    world.entities["hero"] = Entity(
        key="hero",
        kind="character",
        label=params.hero,
        location=place,
        tags={"gender": params.gender, "trait": params.trait, "role": "visitor helper"},
        meters={"breath": 1.0, "steadiness": 1.0},
        memes={"curiosity": 1.3, "care": 1.0, "wonder": 0.8},
    )
    world.entities["helper"] = Entity(
        key="helper",
        kind="character",
        label=helper_display(params.helper),
        location=place,
        tags={"role": "trusted helper"},
        memes={"patience": 1.4, "kindness": 1.3},
    )
    world.entities["spot"] = Entity(
        key="spot",
        kind="place",
        label=place,
        location=place,
        tags={"setting": "fire station"},
        meters={"stillness": 1.2, "warmth": 1.0},
        memes={"safety": 1.2, "duty": 1.1},
    )
    world.entities["cat"] = Entity(
        key="cat",
        kind="animal",
        label=world.cat.label,
        location=place,
        tags={"state": "watching"},
        meters={"shine": 1.4, "distance": 0.3},
        memes={"magic": 1.5, "guidance": 1.0},
    )
    world.entities["relic"] = Entity(
        key="relic",
        kind="object",
        label=world.relic.title,
        location=place,
        tags={"state": "displayed"},
        meters={"glow": 0.8, "attention": 0.7},
        memes={"memory": 1.2, "lesson": 1.0},
    )
    world.entities["locker"] = Entity(
        key="locker",
        kind="object",
        label="the narrow locker",
        location=place,
        tags={"state": "latched"},
        meters={"light_jump": 0.0},
    )
    world.entities["bell"] = Entity(
        key="bell",
        kind="object",
        label="the old station bell",
        location=place,
        tags={"state": "quiet"},
        meters={"ringing": 0.0},
    )
    world.entities["vent"] = Entity(
        key="vent",
        kind="object",
        label="the cracked vent",
        location=place,
        tags={"state": "clean"},
        meters={"soot": 0.0},
    )
    world.facts["setting"] = "fire station"
    world.facts["seed_words"] = "shiny cat"
    world.facts["style"] = "mystery"
    world.facts["features"] = "inner monologue, magic"
    world.facts["problem_kind"] = world.mystery.kind
    return world


def magic_arrival(world: World) -> None:
    hero = world.entities["hero"]
    cat = world.entities["cat"]
    relic = world.entities["relic"]
    hero.add_meme("wonder", 0.8)
    hero.add_meme("attention", 0.6)
    relic.add_meter("glow", 0.3)
    cat.add_meter("shine", 0.2)
    cat.tags["state"] = "guiding"
    world.facts["cat_magic"] = world.cat.magic
    world.event("magic_arrival", world.cat.magic)


def disturb(world: World) -> None:
    hero = world.entities["hero"]
    spot = world.entities["spot"]
    source = world.entities[world.mystery.source]
    hero.add_meme("worry", 1.0)
    hero.add_meme("imagination", 0.8)
    hero.add_meter("breath", -0.3)
    hero.add_meter("steadiness", -0.2)
    spot.add_meter("stillness", -0.4)
    if world.mystery.kind == "pawtrail":
        source.tags["state"] = "ajar"
        source.set_meter("light_jump", 1.0)
    elif world.mystery.kind == "bell_echo":
        source.tags["state"] = "trembling"
        source.set_meter("ringing", 1.0)
    else:
        source.tags["state"] = "dusty"
        source.set_meter("soot", 1.0)
    world.facts["omen"] = world.mystery.omen
    world.facts["risk"] = world.mystery.risk
    world.event("disturbance", world.mystery.omen, world.mystery.risk)


def inner_monologue(world: World) -> None:
    hero = world.entities["hero"]
    thought = world.mystery.thought.format(
        relic_title=world.relic.title,
        legend=world.relic.legend,
    )
    hero.add_meme("reflection", 0.9)
    hero.add_meme("fear_story", 0.7)
    world.facts["thought"] = thought
    world.event("inner_monologue", thought)


def investigate(world: World) -> None:
    hero = world.entities["hero"]
    helper = world.entities["helper"]
    cat = world.entities["cat"]
    hero.add_meme("courage", 0.9)
    hero.add_meme("careful_looking", 1.0)
    helper.add_meme("guidance", 0.9)
    cat.add_meme("guidance", 0.4)
    cat.set_meter("distance", 0.0)
    world.facts["inspect"] = world.mystery.inspect
    world.facts["reveal"] = world.mystery.reveal
    world.event("investigation", world.mystery.inspect, world.mystery.reveal)


def restore(world: World) -> None:
    hero = world.entities["hero"]
    helper = world.entities["helper"]
    spot = world.entities["spot"]
    cat = world.entities["cat"]
    relic = world.entities["relic"]
    source = world.entities[world.mystery.source]

    hero.add_meme("relief", 1.4)
    hero.add_meme("trust", 1.0)
    helper.add_meme("pride", 0.5)
    hero.add_meter("breath", 0.5)
    hero.add_meter("steadiness", 0.5)
    spot.add_meter("stillness", 0.7)
    spot.add_meter("warmth", 0.2)
    relic.add_meter("attention", 0.5)
    cat.add_meter("shine", -0.1)
    cat.tags["state"] = "resting"

    if world.mystery.kind == "pawtrail":
        source.tags["state"] = "clicked shut"
        source.set_meter("light_jump", 0.0)
    elif world.mystery.kind == "bell_echo":
        source.tags["state"] = "peaceful"
        source.set_meter("ringing", 0.0)
    else:
        source.tags["state"] = "covered"
        source.set_meter("soot", 0.0)

    world.facts["helper_action"] = world.remedy.helper_action
    world.facts["repair_action"] = world.remedy.action
    world.facts["repair_result"] = world.remedy.result
    world.event("restoration", world.remedy.action, world.remedy.result)


def simulate(world: World) -> World:
    if world.history:
        return world
    magic_arrival(world)
    disturb(world)
    inner_monologue(world)
    investigate(world)
    restore(world)
    return world


def render_story(world: World) -> str:
    simulate(world)
    she, her, _ = pronouns(world.params.gender)
    hero = world.entities["hero"]
    helper = world.entities["helper"]
    calm_win = hero.memes.get("relief", 0.0) > hero.memes.get("worry", 0.0)

    opening = (
        f"Rain had just finished tapping the windows of the fire station when {world.params.hero}, {article(world.params.trait)} {world.params.trait} child, "
        f"waited in {world.spot.label}. {sentence_case(world.spot.scene)}. Nearby stood {world.relic.display}. Then {world.cat.label} slipped between the boots. "
        f"It was a shiny cat. {world.cat.coat} {world.cat.magic}"
    )
    trouble = (
        f"{world.mystery.omen} {world.params.hero} felt {her} heart jump, but {she} did not run. Inside {she} thought, "
        f"\"{world.facts['thought']}\""
    )
    turn = (
        f"The shiny cat did not vanish. Instead, it paused and let its magic shimmer touch the clue. {sentence_case(helper.label)} came close and spoke in a calm voice. "
        f"{world.mystery.inspect} {world.remedy.helper_action} {world.mystery.reveal} Together they {world.remedy.action}."
    )
    ending_lesson = (
        world.relic.lesson
        if calm_win
        else "Even after the fix, the child kept learning that mysteries shrink when someone looks carefully at the real room."
    )
    ending = (
        f"{world.remedy.result} After that, the fire station sounded like itself again. In the end, {lower_first(world.spot.ending_image)}. "
        f"{world.remedy.image} {world.cat.ending_pose} {sentence_case(world.mystery.ending_change)}. {ending_lesson}"
    )
    return "\n\n".join([opening, trouble, turn, ending])


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a child-friendly mystery set in a fire station that includes the words "shiny cat."',
        f"Tell a magical inner-monologue story about {world.params.hero} following clues in {world.spot.label}.",
        f"Write a mystery where {world.mystery.label} is solved through careful noticing, gentle help, and a magical cat.",
    ]


def story_qa(world: World) -> list[QAItem]:
    simulate(world)
    helper = world.entities["helper"].label
    return [
        QAItem(
            "What made the child think a mystery had begun?",
            f"{world.mystery.omen} That strange sign arrived right after the shiny cat appeared with real magic around it, so the fire station suddenly felt full of clues.",
        ),
        QAItem(
            "What was going through the child's mind?",
            f"{world.params.hero} thought, \"{world.facts['thought']}\" The inner monologue shows how the child turned a small clue into a bigger mystery before the truth was known.",
        ),
        QAItem(
            "How did the shiny cat help without speaking?",
            f"The shiny cat kept close to the right clue and let its magic light the important place. That guidance helped the child inspect the station instead of guessing wildly.",
        ),
        QAItem(
            "What was the real cause of the problem?",
            f"{world.mystery.reveal} So the scary part came from a small physical problem, not from something dangerous hiding in the station.",
        ),
        QAItem(
            "How did the helper change the middle of the story?",
            f"{sentence_case(helper)} made the search steadier by treating the worry kindly. {world.remedy.helper_action} That calm support gave the child room to solve the mystery well.",
        ),
        QAItem(
            "What proves that the ending is calmer than the beginning?",
            f"By the last paragraph, {lower_first(world.spot.ending_image)}. {world.remedy.image} {sentence_case(world.mystery.ending_change)}. Those details show that the room, the child, and the clue have all settled.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    simulate(world)
    items = [
        QAItem(
            "Why does inner monologue work well in a child-sized mystery?",
            "It lets the reader hear how a clue feels before anyone explains it. That makes the later reveal satisfying, because the answer untangles a real worry instead of replacing an empty mood.",
        ),
        QAItem(
            "Why is a fire station a strong setting for a gentle mystery?",
            "A fire station is full of tools, routines, and serious objects that already ask to be noticed. When one tiny thing is out of place, the setting naturally turns that detail into a clue.",
        ),
        QAItem(
            "Why can magic stay child-friendly in a mystery like this?",
            "The magic points toward the truth instead of hiding it. A glowing cat or a shimmered clue can deepen wonder while still leading the child back to a real, fixable cause.",
        ),
    ]
    if world.mystery.kind == "pawtrail":
        items.append(
            QAItem(
                "Why would a lost charm make a corner feel haunted?",
                "Jumping light can make ordinary metal and shadows seem alive. Once the charm is back where it belongs, the same corner becomes readable again.",
            )
        )
    elif world.mystery.kind == "bell_echo":
        items.append(
            QAItem(
                "Why can one small bell sound feel bigger at night?",
                "In a quiet building, a single note has room to echo inside the listener's imagination. If the cause is hidden, the mind often writes a larger story around that small sound.",
            )
        )
    else:
        items.append(
            QAItem(
                "Why can soot on glass turn into a story all by itself?",
                "Marks that appear and vanish invite people to guess at patterns before they inspect the surface. A mystery grows fastest when the eye notices the shape before the hand checks the source.",
            )
        )
    return items


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = render_story(world)
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
combo(S,C,M,R,L) :-
    spot(S),
    cat(C),
    mystery(M),
    remedy(R),
    relic(L),
    mystery_kind(M,K),
    spot_support(S,K),
    cat_support(C,K),
    relic_echo(L,K),
    remedy_kind(R,K).

ok :- chosen(S,C,M,R,L), combo(S,C,M,R,L).

#show combo/5.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    import storyworlds.asp as asp

    rows: list[str] = []
    for key, spot in SPOTS.items():
        rows.append(asp.fact("spot", key))
        for support in spot.supports:
            rows.append(asp.fact("spot_support", key, support))
    for key, cat in CATS.items():
        rows.append(asp.fact("cat", key))
        for support in cat.supports:
            rows.append(asp.fact("cat_support", key, support))
    for key, mystery in MYSTERIES.items():
        rows.append(asp.fact("mystery", key))
        rows.append(asp.fact("mystery_kind", key, mystery.kind))
    for key, remedy in REMEDIES.items():
        rows.append(asp.fact("remedy", key))
        rows.append(asp.fact("remedy_kind", key, remedy.kind))
    for key, relic in RELICS.items():
        rows.append(asp.fact("relic", key))
        for echo in relic.echoes:
            rows.append(asp.fact("relic_echo", key, echo))
    if params is not None:
        rows.append(
            asp.fact(
                "chosen",
                params.spot,
                params.cat,
                params.mystery,
                params.remedy,
                params.relic,
            )
        )
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    return asp_facts(params) + ASP_RULES


def asp_valid_combos() -> set[tuple[str, str, str, str, str]]:
    import storyworlds.asp as asp

    combos: set[tuple[str, str, str, str, str]] = set()
    for model in asp.solve(asp_program(), models=0):
        combos.update(asp.atoms(model, "combo"))
    return combos


def asp_verify(params: StoryParams) -> bool:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program(params))
    return bool(asp.atoms(model, "ok"))


def verify() -> str:
    python_combos = set(valid_combos())
    asp_combos = asp_valid_combos()
    if python_combos != asp_combos:
        raise StoryError(
            f"ASP/Python mismatch. only_python={sorted(python_combos - asp_combos)} "
            f"only_asp={sorted(asp_combos - python_combos)}"
        )

    exercised = 0
    for i, combo in enumerate(sorted(python_combos)):
        params = StoryParams(
            spot=combo[0],
            cat=combo[1],
            mystery=combo[2],
            remedy=combo[3],
            relic=combo[4],
            hero="Mina",
            gender="girl",
            helper="captain",
            trait="observant",
            seed=i,
        )
        if not asp_verify(params):
            raise StoryError(f"ASP rejected Python-valid combo: {combo}")
        sample = generate(params)
        if "shiny cat" not in sample.story:
            raise StoryError(f"Generated story missing seed words for combo: {combo}")
        if "fire station" not in sample.story:
            raise StoryError(f"Generated story missing setting phrase for combo: {combo}")
        if "thought" not in sample.story:
            raise StoryError(f"Generated story missing inner-monologue framing for combo: {combo}")
        if "magic" not in sample.story:
            raise StoryError(f"Generated story missing explicit magic for combo: {combo}")
        if len(sample.story_qa) < 6 or len(sample.world_qa) < 4:
            raise StoryError(f"Generated QA too thin for combo: {combo}")
        exercised += 1
    return (
        f"OK: ASP and Python agree on {len(python_combos)} valid shiny-cat fire-station stories; "
        f"exercised {exercised} samples."
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate shiny-cat fire-station mystery storyworld samples."
    )
    parser.add_argument("--spot", choices=sorted(SPOTS))
    parser.add_argument("--cat", choices=sorted(CATS))
    parser.add_argument("--mystery", choices=sorted(MYSTERIES))
    parser.add_argument("--remedy", choices=sorted(REMEDIES))
    parser.add_argument("--relic", choices=sorted(RELICS))
    parser.add_argument("--hero")
    parser.add_argument("--gender", choices=sorted(HEROES))
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("--seed", type=int)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def matching_combos(args: argparse.Namespace) -> list[tuple[str, str, str, str, str]]:
    rows: list[tuple[str, str, str, str, str]] = []
    for combo in valid_combos():
        if args.spot and args.spot != combo[0]:
            continue
        if args.cat and args.cat != combo[1]:
            continue
        if args.mystery and args.mystery != combo[2]:
            continue
        if args.remedy and args.remedy != combo[3]:
            continue
        if args.relic and args.relic != combo[4]:
            continue
        rows.append(combo)
    return rows


def make_params(
    args: argparse.Namespace,
    rng: random.Random,
    combo: tuple[str, str, str, str, str],
    seed: int | None,
) -> StoryParams:
    gender = args.gender or rng.choice(sorted(HEROES))
    hero = args.hero or rng.choice(HEROES[gender])
    helper = args.helper or rng.choice(HELPERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        spot=combo[0],
        cat=combo[1],
        mystery=combo[2],
        remedy=combo[3],
        relic=combo[4],
        hero=hero,
        gender=gender,
        helper=helper,
        trait=trait,
        seed=seed,
    )


def resolve_params(args: argparse.Namespace, rng: random.Random | None = None) -> StoryParams:
    rng = rng or random.Random(args.seed)
    combos = matching_combos(args)
    if not combos:
        spot = args.spot or next(iter(SPOTS))
        cat = args.cat or next(iter(CATS))
        mystery = args.mystery or next(iter(MYSTERIES))
        remedy = args.remedy or next(iter(REMEDIES))
        relic = args.relic or next(iter(RELICS))
        raise StoryError(explain_rejection(spot, cat, mystery, remedy, relic))
    story_seed = getattr(rng, "story_seed", args.seed)
    return make_params(args, rng, rng.choice(combos), story_seed)


def format_qa(sample: StorySample) -> str:
    lines = ["", "== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story-grounded QA ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge QA ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, args: argparse.Namespace, header: str | None = None) -> None:
    if header:
        print(header)
    print(sample.story)
    if args.trace and sample.world is not None:
        print(sample.world.trace())
    if args.qa:
        print(format_qa(sample))


def json_dump(samples: list[StorySample]) -> None:
    if len(samples) == 1:
        print(samples[0].to_json())
        return
    print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))


def samples_for_all(args: argparse.Namespace) -> list[StorySample]:
    rows: list[StorySample] = []
    base_seed = args.seed if args.seed is not None else 1000
    for i, combo in enumerate(valid_combos()):
        story_seed = base_seed + i
        rng = random.Random(story_seed)
        rng.story_seed = story_seed
        rows.append(generate(make_params(args, rng, combo, story_seed)))
    return rows


def samples_for_n(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)
    target = max(1, args.n)
    rows: list[StorySample] = []
    seen: set[str] = set()
    attempts = 0
    while len(rows) < target and attempts < target * 40:
        story_seed = base_seed + attempts
        rng = random.Random(story_seed)
        rng.story_seed = story_seed
        sample = generate(resolve_params(args, rng))
        if sample.story not in seen:
            seen.add(sample.story)
            rows.append(sample)
        attempts += 1
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.show_asp:
            print(asp_program())
            return 0
        if args.verify:
            print(verify())
            return 0
        if args.asp:
            for combo in sorted(asp_valid_combos()):
                print("\t".join(combo))
            return 0

        samples = samples_for_all(args) if args.all else samples_for_n(args)
        if args.json:
            json_dump(samples)
            return 0
        for i, sample in enumerate(samples):
            header = None
            if args.all:
                header = (
                    f"### {sample.params.hero}: {sample.params.spot} / "
                    f"{sample.params.mystery} / {sample.params.relic}"
                )
            elif len(samples) > 1:
                header = f"### variant {i + 1}"
            emit(sample, args, header)
            if i != len(samples) - 1:
                print("\n" + "=" * 70 + "\n")
        return 0
    except StoryError as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
