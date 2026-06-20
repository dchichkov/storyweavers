#!/usr/bin/env python3
"""
Petting-zoo ghost-story world built from the seed word "shackle".

Internal source tale
--------------------
At Hushbell Petting Zoo, two friends stay for the last brushing round as the
pens turn silver under evening light. A thin shackle clink and one pale moving
shape make the place feel haunted. The hero is frightened, but the friend stays
close, and together with a calm helper they test the scare instead of feeding
it. The ghost always becomes an ordinary petting-zoo problem that friendship
helps them solve, and the ending image proves the fear has left the pens.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


ZOO_NAME = "Hushbell Petting Zoo"


@dataclass(frozen=True)
class Outcome:
    spot: str
    truth: str
    why_here: str
    final_fix: str
    final_image: str


@dataclass(frozen=True)
class Pen:
    key: str
    phrase: str
    detail: str
    ending_image: str
    outcomes: dict[str, Outcome]


@dataclass(frozen=True)
class Haunting:
    key: str
    label: str
    need: str
    sound_phrase: str
    clue: str
    opening_image: str


@dataclass(frozen=True)
class Method:
    key: str
    phrase: str
    action_text: str
    safe_reason: str
    solves: tuple[str, ...]
    unsafe: bool = False


@dataclass(frozen=True)
class Helper:
    key: str
    phrase: str
    comfort_line: str


@dataclass
class StoryParams:
    pen: str
    haunting: str
    method: str
    hero: str
    gender: str
    friend: str
    helper: str
    seed: int | None = None


@dataclass
class Entity:
    name: str
    kind: str
    phrase: str
    location: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.kind in {"girl", "woman"}:
            table = {"subject": "she", "object": "her", "possessive": "her"}
            return table[case]
        if self.kind in {"boy", "man"}:
            table = {"subject": "he", "object": "him", "possessive": "his"}
            return table[case]
        table = {"subject": "they", "object": "them", "possessive": "their"}
        return table[case]


@dataclass
class World:
    params: StoryParams
    pen_cfg: Pen
    haunting_cfg: Haunting
    method_cfg: Method
    helper_cfg: Helper
    outcome_cfg: Outcome
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, str] = field(default_factory=dict)
    history: list[dict[str, str]] = field(default_factory=list)
    fired: list[str] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.name] = entity
        return entity

    def get(self, name: str) -> Entity:
        return self.entities[name]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def event(self, name: str, **data: str) -> None:
        self.history.append({"event": name, **data})
        self.fired.append(name)

    def render(self) -> str:
        return "\n\n".join(" ".join(bits) for bits in self.paragraphs if bits)

    def trace(self) -> str:
        rows = ["--- world model state ---"]
        rows.append(f"  pen={self.pen_cfg.key}")
        rows.append(f"  haunting={self.haunting_cfg.key}")
        rows.append(f"  method={self.method_cfg.key}")
        rows.append(f"  helper={self.helper_cfg.key}")
        for entity in self.entities.values():
            meters = {k: v for k, v in entity.meters.items() if v}
            memes = {k: v for k, v in entity.memes.items() if v}
            rows.append(
                f"  {entity.name}<{entity.kind}> location={entity.location} "
                f"meters={meters} memes={memes}"
            )
        rows.append(f"  facts={self.facts}")
        rows.append(f"  history={self.history}")
        rows.append(f"  fired={self.fired}")
        return "\n".join(rows)


PENS: dict[str, Pen] = {
    "goat_yard": Pen(
        key="goat_yard",
        phrase="the moonlit goat yard by the apple-crate fence",
        detail=(
            "white goats dozed in straw while a pearly lamp swung above the salt lick"
        ),
        ending_image=(
            "The goats settled nose to straw, and the apple-crate fence held one still silver line."
        ),
        outcomes={
            "light": Outcome(
                spot="the tin scoop hook beside the moon gate",
                truth=(
                    "Pepper the goat was reaching through the bars, and his long ear threw a giant shadow while a loose shackle tapped the tin scoop."
                ),
                why_here=(
                    "The lamp hung low behind him, so the shadow looked bigger and farther away than the goat himself."
                ),
                final_fix=(
                    "The helper clipped the shackle flat against the gate and hung the scoop back on its peg."
                ),
                final_image=(
                    "The ghost face folded down into nothing more than Pepper's sleepy head."
                ),
            ),
            "lift": Outcome(
                spot="the brushing stand under the pale grain sack",
                truth=(
                    "A pale grain sack had slipped over the brushing stand, and the loose shackle on the stand kept scratching a metal comb whenever the sack puffed."
                ),
                why_here=(
                    "Each soft breath of air made the sack bow like a nodding ghost, even though the stand beneath it never moved by itself."
                ),
                final_fix=(
                    "They folded the grain sack, set the comb away, and wrapped the shackle so it could not scrape again."
                ),
                final_image=(
                    "Only the plain wooden stand remained, with no white shape left to bow in the dark."
                ),
            ),
            "wait": Outcome(
                spot="the feed bucket by the low moon gate",
                truth=(
                    "A small goat kept nudging the feed bucket from behind the gate, and every nudge made the old shackle click against the latch."
                ),
                why_here=(
                    "The hay pile hid the goat's nose, so the sound arrived before the children could see what was making it."
                ),
                final_fix=(
                    "The bucket went farther inside the pen, and the shackle was fastened high where it could not click."
                ),
                final_image=(
                    "The gate stopped whispering as soon as the bucket stood quiet."
                ),
            ),
        },
    ),
    "pony_stall": Pen(
        key="pony_stall",
        phrase="the pony brushing stall under the yellow rafters",
        detail=(
            "a patient gray pony blinked by the rail while clean brushes waited in a neat row"
        ),
        ending_image=(
            "The gray pony breathed warm clouds into the still stall, and every brush stayed exactly where it belonged."
        ),
        outcomes={
            "light": Outcome(
                spot="the curry-comb peg beside the stall lantern",
                truth=(
                    "Moss the pony had turned his head toward the lantern, and his forelock shadow stretched across the boards while a loose shackle tapped the hanging curry comb."
                ),
                why_here=(
                    "The yellow rafter light bent the forelock into a floating shape, so the shadow looked like a face drifting beside the stall."
                ),
                final_fix=(
                    "The helper hooked the shackle short, steadied the comb rack, and turned the lantern so the shadow fell close to the pony."
                ),
                final_image=(
                    "The long face in the wood broke apart into mane, rail, and quiet lantern shine."
                ),
            ),
            "lift": Outcome(
                spot="the grooming rail under the pale brushing cloth",
                truth=(
                    "A pale brushing cloth had slumped over the rail, and the loose shackle beneath it kept ticking against a tin curry comb."
                ),
                why_here=(
                    "When the cloth puffed and settled, it looked almost alive, but the shape always came from the rail underneath."
                ),
                final_fix=(
                    "They lifted the cloth cleanly, folded it square, and tied the shackle so the metal could not peck at the comb."
                ),
                final_image=(
                    "The stall showed only a folded cloth, a quiet rail, and Moss blinking at nothing strange."
                ),
            ),
            "wait": Outcome(
                spot="the oat pan beside the brushing post",
                truth=(
                    "Moss kept nosing the oat pan when he thought no one was looking, and the pan's rim nudged the old shackle with each hopeful sniff."
                ),
                why_here=(
                    "The stall boards hid the movement at first, so the clink sounded ghostly before the pony stepped fully into view."
                ),
                final_fix=(
                    "The helper moved the oat pan deeper into the stall and looped the shackle away from the rim."
                ),
                final_image=(
                    "Only slow pony chewing stayed in the stall after that."
                ),
            ),
        },
    ),
    "rabbit_garden": Pen(
        key="rabbit_garden",
        phrase="the rabbit garden beside the cabbage path",
        detail=(
            "little hutches sat under climbing beans, and pale watering cans caught the evening glow"
        ),
        ending_image=(
            "The hutches rested under the beans, and the cabbage leaves stopped trembling altogether."
        ),
        outcomes={
            "light": Outcome(
                spot="the latch post beside the watering cans",
                truth=(
                    "Clover the rabbit had stood up behind the mesh, and her tall ears made a wavering shadow while a loose shackle ticked on the latch post."
                ),
                why_here=(
                    "The watering cans threw back the last light, so the ear shadow seemed brighter and farther from the hutch than it really was."
                ),
                final_fix=(
                    "The helper tied the shackle snug to the post and turned the watering cans away from the mesh."
                ),
                final_image=(
                    "The hovering face shrank into two ordinary rabbit ears behind the wire."
                ),
            ),
            "lift": Outcome(
                spot="the carrot-crate bench under the pale feed cloth",
                truth=(
                    "A pale feed cloth had slipped across the carrot-crate bench, and the bench shackle kept ticking against a small scoop under the cloth."
                ),
                why_here=(
                    "The cloth was thin enough to shine and thick enough to hide the bench, which made an ordinary pile look haunted."
                ),
                final_fix=(
                    "They lifted the cloth from both corners, folded it onto the crate, and tucked the shackle where it could not strike the scoop."
                ),
                final_image=(
                    "The bench sat bare and sensible once the cloth was folded away."
                ),
            ),
            "wait": Outcome(
                spot="the carrot pan near the bean trellis",
                truth=(
                    "Clover kept hopping out to nibble from the carrot pan, and each quick bump made the old shackle tap the side rail."
                ),
                why_here=(
                    "The bean leaves hid the hop at first, so the sound seemed to come from empty air."
                ),
                final_fix=(
                    "The pan was moved clear of the rail, and the shackle was tied back against the post."
                ),
                final_image=(
                    "After that, the only soft sound was Clover chewing one last carrot piece."
                ),
            ),
        },
    ),
}

HAUNTINGS: dict[str, Haunting] = {
    "moon_face": Haunting(
        key="moon_face",
        label="the moon-face ghost",
        need="light",
        sound_phrase="a silver clink that answered a pale face in the dark",
        clue="The pale face grew longer or shorter whenever the lantern angle changed.",
        opening_image="One pale shape seemed to hover where no child had been standing a moment before.",
    ),
    "pale_cover": Haunting(
        key="pale_cover",
        label="the pale-cover ghost",
        need="lift",
        sound_phrase="a dragging whisper with a tiny metal tick inside it",
        clue="The white shape sagged when the air rested and swelled when the cloth stirred.",
        opening_image="Something white seemed to bow and rise all by itself.",
    ),
    "hidden_nibbler": Haunting(
        key="hidden_nibbler",
        label="the hidden-nibbler ghost",
        need="wait",
        sound_phrase="a shy clink followed by a secret little munch",
        clue="The sound came a breath after the smell of feed drifted through the pen.",
        opening_image="The dark seemed empty, yet the clink kept answering an unseen mouth.",
    ),
}

METHODS: dict[str, Method] = {
    "lower_lantern_and_look": Method(
        key="lower_lantern_and_look",
        phrase="lower the barn lantern and study the shadow before touching anything",
        action_text="The low light made the edges honest again and kept guessing from doing all the work.",
        safe_reason="looking first is safer than grabbing at a scare in the dark.",
        solves=("light",),
    ),
    "lift_the_cover_together": Method(
        key="lift_the_cover_together",
        phrase="lift the pale cover together from both corners",
        action_text="Two steady hands kept the cloth from snapping or hiding one more surprise.",
        safe_reason="balanced lifting stops a cover from jerking loose and making a bigger fright.",
        solves=("lift",),
    ),
    "wait_with_helper_and_feed": Method(
        key="wait_with_helper_and_feed",
        phrase="stand still with the helper and listen beside the feed bucket",
        action_text="Patience gave the hidden animal time to choose the open instead of the shadows.",
        safe_reason="stillness lets animals show themselves without anyone chasing them.",
        solves=("wait",),
    ),
    "yank_at_the_noise": Method(
        key="yank_at_the_noise",
        phrase="yank at the noise before anyone can think",
        action_text="That would only turn fear into rough hands.",
        safe_reason="Rough grabbing can scare animals and tangle equipment.",
        solves=("light", "lift", "wait"),
        unsafe=True,
    ),
}

HELPERS: dict[str, Helper] = {
    "mrs_vale": Helper(
        key="mrs_vale",
        phrase="Mrs. Vale, the evening keeper",
        comfort_line="Keep your feet flat and your hearts slow, and the truth will come closer than the scare.",
    ),
    "tomas": Helper(
        key="tomas",
        phrase="Tomas, the brushing helper",
        comfort_line="A petting zoo likes gentle hands best. When we stay gentle, even a ghost story has to tell the truth.",
    ),
    "aunt_jo": Helper(
        key="aunt_jo",
        phrase="Aunt Jo, who carried the feed pail",
        comfort_line="Listen before you leap. Night sounds are often only small chores asking to be noticed.",
    ),
}

HERO_NAMES = {
    "girl": ("Mina", "Elsie", "Ruth", "Poppy"),
    "boy": ("Owen", "Nico", "Jude", "Felix"),
}

FRIEND_NAMES = (
    "June",
    "Milo",
    "Tess",
    "Ari",
    "Nell",
    "Remy",
)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for pen in PENS.values():
        for haunting in HAUNTINGS.values():
            if haunting.need not in pen.outcomes:
                continue
            for method in METHODS.values():
                if method.unsafe:
                    continue
                if haunting.need in method.solves:
                    combos.append((pen.key, haunting.key, method.key))
    return sorted(combos)


def explain_rejection(pen: str, haunting: str, method: str) -> str:
    if pen not in PENS:
        return f"Unknown pen '{pen}'."
    if haunting not in HAUNTINGS:
        return f"Unknown haunting '{haunting}'."
    if method not in METHODS:
        return f"Unknown method '{method}'."
    haunting_cfg = HAUNTINGS[haunting]
    method_cfg = METHODS[method]
    if method_cfg.unsafe:
        return (
            f"No story: {method_cfg.phrase} is not a reasonable choice in a petting zoo because "
            f"{method_cfg.safe_reason.lower()}"
        )
    if haunting_cfg.need not in method_cfg.solves:
        return (
            f"No story: {method_cfg.phrase} cannot solve {haunting_cfg.label} because that scare needs "
            f"a {haunting_cfg.need}-based test."
        )
    if haunting_cfg.need not in PENS[pen].outcomes:
        return (
            f"No story: {PENS[pen].phrase} does not support the {haunting_cfg.need} clue needed for "
            f"{haunting_cfg.label}."
        )
    return "No story: those options do not form a reasonable ghost story."


def build_world(params: StoryParams) -> World:
    if params.hero == params.friend:
        raise StoryError("No story: the friend must be a different child from the hero.")
    reason = explain_rejection(params.pen, params.haunting, params.method)
    if not reason.startswith("No story: those options do not form"):
        if (params.pen, params.haunting, params.method) not in valid_combos():
            raise StoryError(reason)
    pen_cfg = PENS[params.pen]
    haunting_cfg = HAUNTINGS[params.haunting]
    method_cfg = METHODS[params.method]
    if method_cfg.unsafe:
        raise StoryError(reason)
    if haunting_cfg.need not in method_cfg.solves:
        raise StoryError(reason)
    outcome_cfg = pen_cfg.outcomes[haunting_cfg.need]
    helper_cfg = HELPERS[params.helper]
    world = World(
        params=params,
        pen_cfg=pen_cfg,
        haunting_cfg=haunting_cfg,
        method_cfg=method_cfg,
        helper_cfg=helper_cfg,
        outcome_cfg=outcome_cfg,
    )
    hero = world.add(Entity(params.hero, params.gender, f"a careful {params.gender}", location=pen_cfg.phrase))
    friend = world.add(Entity(params.friend, "child", "a loyal friend", location=pen_cfg.phrase))
    helper = world.add(Entity(helper_cfg.phrase, "adult", "a calm helper", location=pen_cfg.phrase))
    shackle = world.add(Entity("shackle", "object", "the old metal shackle", location=outcome_cfg.spot))
    animal_name = animal_name_for(outcome_cfg.truth)
    animal = world.add(Entity(animal_name, "animal", "a gentle petting-zoo animal", location=pen_cfg.phrase))
    hero.meters["steady"] = 0.56
    hero.meters["fear"] = 0.18
    hero.memes["Friendship"] = 0.82
    hero.memes["Curiosity"] = 0.68
    friend.meters["steady"] = 0.72
    friend.memes["Friendship"] = 0.9
    helper.memes["Care"] = 0.88
    shackle.meters["looseness"] = 0.71
    animal.meters["restlessness"] = 0.35
    world.facts.update(
        {
            "resolved": "no",
            "ghost_name": haunting_cfg.label,
            "need": haunting_cfg.need,
            "spot": outcome_cfg.spot,
            "helper_line": helper_cfg.comfort_line,
            "method_reason": method_cfg.safe_reason,
            "animal": animal_name,
            "friendship_result": "forming",
        }
    )
    world.event("world_built", pen=pen_cfg.key, haunting=haunting_cfg.key, method=method_cfg.key)
    return world


def animal_name_for(truth: str) -> str:
    if "Pepper" in truth:
        return "Pepper"
    if "Moss" in truth:
        return "Moss"
    if "Clover" in truth:
        return "Clover"
    return "the animal"


def lower_first(text: str) -> str:
    if not text:
        return text
    return text[:1].lower() + text[1:]


def enact_premise(world: World) -> None:
    hero = world.get(world.params.hero)
    friend = world.get(world.params.friend)
    hero.location = world.pen_cfg.phrase
    friend.location = world.pen_cfg.phrase
    world.say(
        f"On the last quiet round at {ZOO_NAME}, {hero.name} and {friend.name} walked into {world.pen_cfg.phrase}, "
        f"where {world.pen_cfg.detail}."
    )
    world.say(
        f"They had promised to keep each other brave all evening, and that simple friendship promise made the dim place feel warm instead of lonely."
    )
    world.say(
        f"{hero.name} liked ghost stories in books, but the real petting zoo sounded different after sunset."
    )
    world.event("premise", hero=hero.name, friend=friend.name, pen=world.pen_cfg.key)


def hear_the_ghost(world: World) -> None:
    hero = world.get(world.params.hero)
    friend = world.get(world.params.friend)
    hero.meters["fear"] += 0.43
    hero.meters["steady"] -= 0.18
    world.para()
    world.say(
        f"Then the children heard {world.haunting_cfg.sound_phrase}, and the old shackle seemed to answer from {world.outcome_cfg.spot}."
    )
    world.say(world.haunting_cfg.opening_image)
    world.say(
        f"{hero.name} caught {friend.name}'s sleeve and whispered that the yard felt like a true ghost story. {world.haunting_cfg.clue}"
    )
    world.event("haunting_heard", sound=world.haunting_cfg.sound_phrase, clue=world.haunting_cfg.clue)


def investigate(world: World) -> None:
    hero = world.get(world.params.hero)
    friend = world.get(world.params.friend)
    helper = world.get(world.helper_cfg.phrase)
    hero.location = world.outcome_cfg.spot
    friend.location = world.outcome_cfg.spot
    helper.location = world.outcome_cfg.spot
    hero.memes["Friendship"] += 0.12
    friend.memes["Friendship"] += 0.08
    hero.meters["steady"] += 0.22
    hero.meters["fear"] -= 0.17
    world.para()
    world.say(
        f"But {friend.name} did not laugh or run. Instead, {friend.pronoun('subject')} moved shoulder to shoulder with {hero.name} and called for {world.helper_cfg.phrase}."
    )
    world.say(world.helper_cfg.comfort_line)
    world.say(
        f"So the three of them chose to {world.method_cfg.phrase}. {world.method_cfg.action_text}"
    )
    world.say(
        f"The choice fit the moment because {world.method_cfg.safe_reason}"
    )
    world.event("investigation", helper=world.helper_cfg.key, method=world.method_cfg.key)


def resolve_ghost(world: World) -> None:
    hero = world.get(world.params.hero)
    friend = world.get(world.params.friend)
    shackle = world.get("shackle")
    animal = world.get(world.facts["animal"])
    hero.meters["fear"] = max(0.0, hero.meters["fear"] - 0.31)
    hero.meters["steady"] += 0.24
    hero.memes["Friendship"] += 0.2
    friend.memes["Friendship"] += 0.12
    shackle.meters["looseness"] = 0.0
    animal.meters["restlessness"] = 0.08
    world.facts["resolved"] = "yes"
    world.facts["friendship_result"] = "proved"
    world.para()
    world.say(
        f"At {world.outcome_cfg.spot}, the ghost gave up its secret. {world.outcome_cfg.truth}"
    )
    world.say(world.outcome_cfg.why_here)
    world.say(world.outcome_cfg.final_fix)
    world.say(
        f"{hero.name} let out a shaky laugh because the haunting was only a small problem with light, cloth, or feed, not a spirit at all. "
        f"{friend.name} stayed close until the fear had nowhere left to stand."
    )
    world.say(
        f"In the end, the children felt proud of their friendship for choosing kindness over panic. "
        f"{world.pen_cfg.ending_image} {world.outcome_cfg.final_image}"
    )
    world.event("resolved", truth=world.outcome_cfg.truth, spot=world.outcome_cfg.spot)


def story_text(world: World) -> str:
    return world.render()


def prompts_for(world: World) -> list[str]:
    return [
        'Write a child-friendly ghost story set in a petting zoo that includes the word "shackle".',
        "Give the hero one close friend and one calm helper so the middle turn is driven by friendship instead of panic.",
        "End with a concrete image that proves the ghostly scare has become an ordinary solved problem in the animal pens.",
    ]


def story_qa_for(world: World) -> list[QAItem]:
    hero = world.get(world.params.hero)
    friend = world.get(world.params.friend)
    return [
        QAItem(
            "Why did the petting zoo start to feel haunted?",
            f"The petting zoo felt haunted because {world.haunting_cfg.sound_phrase} came out of the dark while one pale shape moved in a confusing way. The loose shackle and the half-seen image reached {hero.name} before the real cause did, so the scare felt larger than it was.",
        ),
        QAItem(
            "What part did friendship play when the fear first rose?",
            f"Friendship mattered right away because {friend.name} stayed beside {hero.name} instead of teasing or running off. That steady company gave {hero.name} enough calm to test the ghost rather than simply believe in it.",
        ),
        QAItem(
            "How did the children investigate safely?",
            f"They investigated by choosing to {world.method_cfg.phrase}. That method matched the clue in the world, and it protected both the children and the animals from rough, frightened grabbing.",
        ),
        QAItem(
            "What was the ghost really?",
            f"The ghost was not a spirit at all. {world.outcome_cfg.truth} Once the children could see the cause clearly, the whole haunting shrank into an ordinary petting-zoo problem.",
        ),
        QAItem(
            "Why did the strange sight look so real at first?",
            f"It looked real at first because {lower_first(world.outcome_cfg.why_here)} The darkness hid the plain shape underneath, so the children saw a ghostly picture before they saw the true object or animal.",
        ),
        QAItem(
            "How does the ending prove that the scare is over?",
            f"The ending proves the scare is over because the shackle is fixed, the animals are calm, and the pen returns to an ordinary quiet rhythm. The final image is peaceful instead of jumpy, which shows that truth and friendship have both done their work.",
        ),
    ]


def world_qa_for(world: World) -> list[QAItem]:
    items = [
        QAItem(
            "Why is it smart to test a scary sound before naming it a ghost?",
            "A tested clue can be seen, touched, or explained in the real place where it happened. That keeps a frightened guess from becoming the loudest thing in the story.",
        ),
        QAItem(
            "How can friendship help in a frightening place?",
            "A good friend can lend calm, share attention, and slow a panic down into a plan. That makes the world easier to read truthfully.",
        ),
        QAItem(
            "Why should children avoid yanking at a strange noise in a petting zoo?",
            "Rough grabbing can frighten animals and tangle the very object that needs to be understood. Gentle investigation keeps both the animals and the children safer.",
        ),
    ]
    if world.haunting_cfg.need == "light":
        items.append(
            QAItem(
                "Why can a low lantern reveal the truth of a shadow?",
                "A changed light angle shows where a shadow truly begins and ends. Once the edges line up with the real animal or object, the haunting loses its disguise.",
            )
        )
    elif world.haunting_cfg.need == "lift":
        items.append(
            QAItem(
                "Why lift a pale cover from both corners?",
                "Two corners keep the cover balanced and stop it from flapping back into a frightening shape. Balanced lifting also shows what solid object is hiding beneath the cloth.",
            )
        )
    else:
        items.append(
            QAItem(
                "Why does waiting help when an animal may be making the sound?",
                "Waiting gives the animal time to repeat its ordinary habit without being chased. That turns a spooky noise into a visible cause and effect.",
            )
        )
    return items


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    enact_premise(world)
    hear_the_ghost(world)
    investigate(world)
    resolve_ghost(world)
    story = story_text(world)
    return StorySample(
        params=params,
        story=story,
        prompts=prompts_for(world),
        story_qa=story_qa_for(world),
        world_qa=world_qa_for(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        print("\n")
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Petting-zoo friendship ghost-story world.")
    parser.add_argument("--pen", choices=sorted(PENS))
    parser.add_argument("--haunting", choices=sorted(HAUNTINGS))
    parser.add_argument("--method", choices=sorted(METHODS))
    parser.add_argument("--hero")
    parser.add_argument("--gender", choices=sorted(HERO_NAMES))
    parser.add_argument("--friend")
    parser.add_argument("--helper", choices=sorted(HELPERS))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        combo
        for combo in valid_combos()
        if (args.pen is None or combo[0] == args.pen)
        and (args.haunting is None or combo[1] == args.haunting)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError(
            explain_rejection(
                args.pen or "goat_yard",
                args.haunting or "moon_face",
                args.method or "lower_lantern_and_look",
            )
        )
    pen, haunting, method = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(sorted(HERO_NAMES))
    hero = args.hero or rng.choice(HERO_NAMES[gender])
    friend_choices = [name for name in FRIEND_NAMES if name != hero]
    friend = args.friend or rng.choice(friend_choices)
    helper = args.helper or rng.choice(sorted(HELPERS))
    return StoryParams(
        pen=pen,
        haunting=haunting,
        method=method,
        hero=hero,
        gender=gender,
        friend=friend,
        helper=helper,
    )


ASP_RULES = r"""
combo(P,H,M) :-
  pen(P), haunting(H), method(M),
  haunting_need(H,N), pen_need(P,N), method_solves(M,N),
  not method_unsafe(M).

#show combo/3.
"""


def asp_facts() -> str:
    from storyworlds import asp

    rows: list[str] = []
    for pen in PENS.values():
        rows.append(asp.fact("pen", pen.key))
        for need in pen.outcomes:
            rows.append(asp.fact("pen_need", pen.key, need))
    for haunting in HAUNTINGS.values():
        rows.append(asp.fact("haunting", haunting.key))
        rows.append(asp.fact("haunting_need", haunting.key, haunting.need))
    for method in METHODS.values():
        rows.append(asp.fact("method", method.key))
        if method.unsafe:
            rows.append(asp.fact("method_unsafe", method.key))
        for need in method.solves:
            rows.append(asp.fact("method_solves", method.key, need))
    return "\n".join(rows)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    from storyworlds import asp

    model = asp.one_model(asp_program("#show combo/3."))
    return sorted(set(asp.atoms(model, "combo")))


def exercise_generated_stories() -> list[str]:
    problems: list[str] = []
    helpers = sorted(HELPERS)
    for i, combo in enumerate(valid_combos()):
        params = StoryParams(
            pen=combo[0],
            haunting=combo[1],
            method=combo[2],
            hero="Mina",
            gender="girl",
            friend="June",
            helper=helpers[i % len(helpers)],
            seed=4000 + i,
        )
        sample = generate(params)
        story = sample.story
        if "shackle" not in story.lower():
            problems.append(f"{combo}: story is missing the seed word 'shackle'")
        if "petting zoo" not in story.lower():
            problems.append(f"{combo}: story does not name the petting zoo setting")
        if "ghost" not in story.lower():
            problems.append(f"{combo}: story never names the ghostly scare")
        if "friendship" not in story.lower():
            problems.append(f"{combo}: story does not foreground friendship")
        if story.count("\n\n") < 2:
            problems.append(f"{combo}: story is missing a clear beginning, turn, or ending paragraph")
        if len(sample.story_qa) < 5:
            problems.append(f"{combo}: story QA set is too small")
        if len(sample.world_qa) < 3:
            problems.append(f"{combo}: world QA set is too small")
        if any(answer.answer.count(".") < 2 for answer in sample.story_qa):
            problems.append(f"{combo}: a story-grounded QA answer is too short")
        if sample.world is None or sample.world.facts.get("resolved") != "yes":
            problems.append(f"{combo}: world never reaches a resolved state")
        if sample.world is not None and sample.world.get(params.hero).memes["Friendship"] <= 0.82:
            problems.append(f"{combo}: friendship does not grow through the turn")
        if "{" in story or "}" in story or "meters=" in story:
            problems.append(f"{combo}: story leaked scaffolding or debug text")
    return problems


def asp_verify() -> int:
    py = set(valid_combos())
    logic = set(asp_valid_combos())
    status = 0
    if py == logic:
        print(f"OK: ASP gate matches Python valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH between Python and ASP gate")
        if py - logic:
            print(f"  only python: {sorted(py - logic)}")
        if logic - py:
            print(f"  only asp: {sorted(logic - py)}")
        status = 1

    problems = exercise_generated_stories()
    if problems:
        print("Story exercise failures:")
        for item in problems:
            print(f"  {item}")
        status = 1
    else:
        print("OK: generated stories pass seed, structure, QA, and resolution checks.")
    return status


def _sample_n(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)
    samples: list[StorySample] = []
    seen: set[str] = set()
    target = max(1, args.n)
    attempts = 0
    while len(samples) < target and attempts < target * 40:
        seed = base_seed + attempts
        attempts += 1
        params = resolve_params(args, random.Random(seed))
        params.seed = seed
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    if len(samples) < target:
        raise StoryError("Not enough unique stories from the current petting zoo constraints.")
    return samples


def _sample_all(args: argparse.Namespace) -> list[StorySample]:
    rows: list[StorySample] = []
    base_seed = args.seed if args.seed is not None else 41
    helpers = sorted(HELPERS)
    for i, combo in enumerate(valid_combos()):
        params = StoryParams(
            pen=combo[0],
            haunting=combo[1],
            method=combo[2],
            hero="Mina",
            gender="girl",
            friend="June",
            helper=helpers[i % len(helpers)],
            seed=base_seed + i,
        )
        rows.append(generate(params))
    return rows


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    if args.show_asp:
        print(asp_program("#show combo/3."))
        return 0
    if args.verify:
        return asp_verify()
    if args.asp:
        for combo in asp_valid_combos():
            print("\t".join(combo))
        return 0

    if args.all:
        samples = _sample_all(args)
    else:
        samples = _sample_n(args)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return 0

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
