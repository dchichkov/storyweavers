#!/usr/bin/env python3
"""
A small storyworld about a child's performance, with a flashback, a moral turn,
and a little humor, told in a rhyming-story style.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Stage:
    place: str = "the little school stage"
    audience: str = "the children and parents"
    props: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    name: str
    gender: str
    helper: str
    prop: str
    seed: Optional[int] = None
    performance: Optional[str] = None
    flashback: Optional[str] = None
    moral: Optional[str] = None
    rhyme_form: Optional[str] = None
    scene_order: Optional[str] = None
    resolution: Optional[str] = None


@dataclass(frozen=True)
class PerformanceArc:
    key: str
    title: str
    place: str
    audience: str
    opening: str
    disruption: str
    cause: str
    recovery: str
    ending_images: tuple[str, ...]


@dataclass(frozen=True)
class FlashbackPath:
    key: str
    memory: str
    remembered_skill: str
    function: str


@dataclass(frozen=True)
class MoralPath:
    key: str
    temptation: str
    choice: str
    value: str
    lesson: str


NAMES_GIRL = ["Mia", "Lina", "Nora", "Zoe", "Ava", "Ivy"]
NAMES_BOY = ["Leo", "Ben", "Max", "Noah", "Sam", "Finn"]
HELPERS = ["friend", "teacher", "sibling"]
PROPS = ["big red hat", "glittery scarf", "toy microphone", "paper crown"]

PERFORMANCES = [
    PerformanceArc(
        key="poem_relay",
        title="moon-poem relay",
        place="the library's moonlit reading corner",
        audience="families on patchwork cushions",
        opening="For a moon-poem relay performance, {name} carried the final verse while each reader passed the poem along like a silver thread.",
        disruption="At the word 'crater,' the page slipped beneath the {prop}, and the final four lines vanished from view.",
        cause="The page had not disappeared; a puff from the floor fan had folded it backward.",
        recovery="{name} unfolded the page, then spoke the last verse slowly enough for every listener to join the final rhyme.",
        ending_images=(
            "The rescued page rested beneath a smooth stone, while paper moons turned above the quiet cushions.",
            "Outside the window, the real moon hung over a row of smiling faces and one safely weighted poem.",
            "The silver paper stars stopped trembling just as the final whispered rhyme faded away.",
        ),
    ),
    PerformanceArc(
        key="puppet_play",
        title="sock-puppet sea play",
        place="the classroom puppet theater",
        audience="younger children sitting cross-legged",
        opening="Behind a blue-cloth sea, {name} raised a sock-puppet captain and began a stormy little performance.",
        disruption="The puppet's yarn mustache caught on the {prop}, leaving the captain dangling upside down above the waves.",
        cause="A loose loop of yarn had hooked the prop when {name} swept the puppet through the pretend storm.",
        recovery="{name} made the upside-down captain part of the adventure, freed the yarn in character, and sailed the puppet safely home.",
        ending_images=(
            "The puppet captain bowed from a cardboard boat, with its mustache finally pointing toward the painted sea.",
            "A last paper wave flopped flat as the children saluted the brave, slightly crooked captain.",
            "The blue cloth settled, and the freed mustache curled like a tiny question mark above the boat.",
        ),
    ),
    PerformanceArc(
        key="kitchen_band",
        title="kitchen-band concert",
        place="the community-room stage",
        audience="neighbors gathered after supper",
        opening="{name} lifted two wooden spoons to conduct a kitchen-band performance of pots, jars, and one bright triangle.",
        disruption="On the grand CLANG, a spoon shot into the {prop}, and the band lost its beat in a jumble of ting-tang-tong.",
        cause="The players had been watching the flying spoon instead of {name}'s counting hands.",
        recovery="{name} turned the clatter into a new four-beat rhythm, counted everyone back in, and brought the tune home together.",
        ending_images=(
            "The final triangle note floated above a neat row of spoons, bowls, and proud kitchen musicians.",
            "One wooden spoon lay inside the {prop}, kept there as the band's funniest souvenir.",
            "The pots shone under the lights while four tapping feet held the recovered beat.",
        ),
    ),
    PerformanceArc(
        key="shadow_play",
        title="forest shadow play",
        place="the school's assembly hall",
        audience="parents beneath strings of leaf-shaped lights",
        opening="For a forest shadow performance, {name} moved paper owls and foxes across a glowing white screen.",
        disruption="A round shadow from the {prop} swallowed the paper moon, and the fox lost the path home.",
        cause="The prop had rolled between the lamp and screen, making a shadow much larger than itself.",
        recovery="{name} let the giant shadow become a friendly eclipse, moved it aside at sunrise, and guided the fox home by starlight.",
        ending_images=(
            "The paper fox curled beneath a restored moon as the lamp clicked softly off.",
            "Tiny leaf shadows trembled around the fox's cardboard den when the screen faded dark.",
            "The last bright circle on the screen became a sunrise, then shrank to a golden pinprick.",
        ),
    ),
    PerformanceArc(
        key="magic_show",
        title="small magic show",
        place="the summer-fair gazebo",
        audience="children holding lemonade cups",
        opening="At a small magic performance, {name} promised to make a ribbon travel through the {prop} without using glue.",
        disruption="The ribbon emerged wearing three paper clips and a label that read CABBAGE, which was not the planned miracle.",
        cause="The ribbon had wandered through the craft box beneath the table instead of through its secret paper tube.",
        recovery="{name} showed the muddled craft box, reset the tube where everyone could see, and performed the simple trick honestly on a second try.",
        ending_images=(
            "The clean ribbon streamed from the {prop}, while the CABBAGE label earned a place on the magician's table.",
            "Three paper clips glittered beside the honest little trick as lemonade cups rose in applause.",
            "The ribbon curled across the gazebo floor, bright, unknotted, and completely free of cabbage.",
        ),
    ),
    PerformanceArc(
        key="rain_dance",
        title="puddle-step dance",
        place="the covered playground",
        audience="classmates lined along the dry wall",
        opening="Rain tapped the roof while {name} began a puddle-step dance performance, swinging the {prop} on every second beat.",
        disruption="A sneaker squeaked half a beat early, and the next turn became an unexpected sit-down slide.",
        cause="A thin ribbon of rain had blown under the roof and made one painted floor tile slick.",
        recovery="{name} marked the wet tile, changed the dance into seated taps and careful steps, and finished where the floor was dry.",
        ending_images=(
            "Raindrops drummed overhead as the dancers' shoes formed a safe, shining row by the wall.",
            "The wet tile reflected the {prop}, a yellow caution cone, and one triumphant final pose.",
            "Beyond the roof, a real puddle held the upside-down reflection of the bowing dancers.",
        ),
    ),
    PerformanceArc(
        key="joke_recital",
        title="riddle-and-joke recital",
        place="the bookshop's tiny platform",
        audience="shoppers between the picture-book shelves",
        opening="For a riddle performance, {name} placed the {prop} beside a jar of question cards and promised one truly terrible joke.",
        disruption="The punch-line card was blank, so the joke stopped at, 'Why did the pancake...' and went nowhere at all.",
        cause="The ink had rubbed onto the card behind it, which now held two punch lines and no beginning.",
        recovery="{name} admitted the ending was missing, asked the audience to invent one, and built their silliest answer into the show.",
        ending_images=(
            "The blank card filled with penciled pancake jokes and leaned proudly against the {prop}.",
            "The question jar rattled with new riddles while one double-printed card dried beside the register.",
            "Between two picture books, the rescued punch line sat under a sketch of a pancake in boots.",
        ),
    ),
    PerformanceArc(
        key="nature_pageant",
        title="garden-creature pageant",
        place="the greenhouse learning garden",
        audience="families seated on straw mats",
        opening="Wearing the {prop}, {name} narrated a garden-creature performance as ladybugs, worms, and bees crossed a leafy stage.",
        disruption="The cardboard bee lost a wing and spun into the lettuce with a soft and very un-beelike plop.",
        cause="One reusable paper fastener had worked loose after many rehearsals.",
        recovery="{name} paused the pageant, borrowed a safe fastener, credited {helper}, and let the repaired bee pollinate the final flower.",
        ending_images=(
            "The mended bee rested on a giant paper sunflower while real leaves brushed the edge of the stage.",
            "A spare brass fastener gleamed beside the {prop} as the cardboard garden took its bow.",
            "The final paper flower opened beneath the greenhouse glass, with two sturdy bee wings above it.",
        ),
    ),
    PerformanceArc(
        key="bell_choir",
        title="handbell morning song",
        place="the town hall steps",
        audience="early visitors wrapped in bright coats",
        opening="At the morning performance, {name} waited to ring the smallest handbell while the {prop} kept the music cards from blowing away.",
        disruption="The smallest bell made no ding at all; it answered the melody with a solemn little thunk.",
        cause="Its soft clapper had twisted sideways during the walk to the steps.",
        recovery="{name} signaled a pause, straightened the clapper with {helper}, and let the quiet beat become a rest before the song returned.",
        ending_images=(
            "The repaired bell gave one clear silver note that seemed to polish the cold morning air.",
            "Music cards fluttered beneath the {prop} as the smallest bell rang the final answer.",
            "On the stone step, the little bell reflected red coats, blue sky, and {name}'s relieved smile.",
        ),
    ),
    PerformanceArc(
        key="costume_tale",
        title="traveling-trunk tale",
        place="the museum story room",
        audience="children gathered around an old travel trunk",
        opening="For a one-child theater performance, {name} used the {prop} to become the captain of a cardboard cloud ship.",
        disruption="The cloud ship's wheel came free, rolled across the rug, and stopped beneath an audience chair.",
        cause="A cardboard pin had bent when the trunk lid pressed against the wheel before the show.",
        recovery="{name} asked for the wheel back, turned the search into a voyage through the audience, and repaired the pin before landing the ship.",
        ending_images=(
            "The cloud ship rested beside the closed trunk, its wheel held straight by a fresh cardboard pin.",
            "A paper cloud hung over the {prop} while the captain's wheel made one last slow turn.",
            "The travel trunk clicked shut on a repaired ship, a folded sky, and tomorrow's adventure.",
        ),
    ),
]

FLASHBACKS = [
    FlashbackPath(
        key="counting",
        memory="During rehearsal, {helper} had tapped four steady beats on a chair: 'Breathe for one, begin on four.'",
        remembered_skill="the four-count and took one calm breath before acting",
        function="recover the rhythm instead of rushing",
    ),
    FlashbackPath(
        key="kind_mistake",
        memory="The day before, {helper} had mixed up two lines, laughed gently, and started again without blaming anyone.",
        remembered_skill="the kind way {helper} had restarted after a mistake",
        function="treat a mistake as something repairable, not shameful",
    ),
    FlashbackPath(
        key="prop_repair",
        memory="At practice, {name} and {helper} had repaired a torn program with tape, testing each fold before the next.",
        remembered_skill="the patient check-and-repair steps from rehearsal",
        function="inspect the real cause before guessing",
    ),
    FlashbackPath(
        key="honest_promise",
        memory="Before dress rehearsal, {name} had promised {helper}: 'If something goes wrong, I will say what happened and ask for help.'",
        remembered_skill="the promise to speak before worry could invent an excuse",
        function="choose honesty under pressure",
    ),
    FlashbackPath(
        key="open_space",
        memory="While practicing, {helper} had left one empty beat in every verse and called it 'a little doorway for surprises.'",
        remembered_skill="the empty beat that could hold an unexpected moment",
        function="adapt the performance without hiding the problem",
    ),
]

MORALS = [
    MoralPath(
        key="honesty",
        temptation="For a blink, {name} wanted to pretend the trouble belonged in the act.",
        choice="Instead, {name} told the audience exactly what had gone wrong and asked for a moment to mend it.",
        value="honesty",
        lesson="telling the truth makes room for a real solution",
    ),
    MoralPath(
        key="share_spotlight",
        temptation="{name} could have guarded the spotlight and struggled alone.",
        choice="Instead, {name} invited {helper} into the performance and thanked that helper by name.",
        value="sharing credit",
        lesson="a shared success can shine brighter than a lonely one",
    ),
    MoralPath(
        key="perseverance",
        temptation="The nearest curtain suddenly looked like a fine place to quit.",
        choice="{name} chose one small next step, then another, until the performance could continue.",
        value="perseverance",
        lesson="bravery can mean trying the next careful step",
    ),
    MoralPath(
        key="care_for_others",
        temptation="A few surprised giggles rose, and {name} nearly answered them with an angry joke.",
        choice="Instead, {name} made a joke about the muddle, not about any person, so everyone could laugh safely together.",
        value="kind humor",
        lesson="the kindest joke lets everyone keep their dignity",
    ),
    MoralPath(
        key="teamwork",
        temptation="{name} tugged once at the problem alone, but that only made the tangle worse.",
        choice="Then {name} stopped, gave {helper} one clear task, and listened when that helper suggested the next move.",
        value="teamwork",
        lesson="good teamwork needs both asking and listening",
    ),
]

RHYME_FORMS = ["couplets", "refrain", "call_response", "comic_triplet"]
SCENE_ORDERS = ["trouble_then_memory", "prop_opens_memory", "helper_cue", "memory_first"]
RESOLUTIONS = ["audience_joins", "mistake_becomes_art", "quiet_reset", "helper_handoff"]


@dataclass
class World:
    stage: Stage
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        return World(stage=copy.deepcopy(self.stage),
                     entities=copy.deepcopy(self.entities),
                     paragraphs=[[]],
                     facts=copy.deepcopy(self.facts),
                     fired=set(self.fired))


def mood_word(m: float) -> str:
    if m >= 2:
        return "very brave"
    if m >= 1:
        return "brave"
    if m <= -1:
        return "nervous"
    return "a little nervous"


def _by_key(items, key: str):
    return next(item for item in items if item.key == key)


def complete_params(params: StoryParams) -> None:
    seed = params.seed
    if seed is None:
        seed = sum(ord(ch) for ch in f"{params.name}|{params.helper}|{params.prop}")
    rng = random.Random(seed ^ 0x5A17C0DE)
    params.performance = params.performance or rng.choice(PERFORMANCES).key
    params.flashback = params.flashback or rng.choice(FLASHBACKS).key
    params.moral = params.moral or rng.choice(MORALS).key
    params.rhyme_form = params.rhyme_form or rng.choice(RHYME_FORMS)
    params.scene_order = params.scene_order or rng.choice(SCENE_ORDERS)
    params.resolution = params.resolution or rng.choice(RESOLUTIONS)


def build_world(params: StoryParams) -> World:
    complete_params(params)
    arc = _by_key(PERFORMANCES, params.performance)
    memory = _by_key(FLASHBACKS, params.flashback)
    moral = _by_key(MORALS, params.moral)
    stage = Stage(place=arc.place, audience=arc.audience, props=[params.prop])
    w = World(stage=stage)
    child = w.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"nervous": 0.0, "joy": 0.0, "confidence": 0.0},
        memes={"hope": 0.0, "humor": 0.0, "moral": 0.0},
    ))
    helper = w.add(Entity(
        id="helper",
        kind="character",
        type=params.helper,
        label=params.helper,
        meters={"kindness": 1.0},
        memes={"care": 1.0},
    ))
    prop = w.add(Entity(
        id="prop",
        type="thing",
        label=params.prop,
        owner=child.id,
    ))
    helper_phrase = {
        "friend": "a friend",
        "teacher": "the teacher",
        "sibling": "their sibling",
    }[params.helper]
    w.facts.update(
        child=child,
        helper=helper,
        helper_phrase=helper_phrase,
        prop=prop,
        params=params,
        arc=arc,
        memory=memory,
        moral=moral,
        ending=arc.ending_images[seeded_index(params, len(arc.ending_images), 11)],
    )
    return w


def seeded_index(params: StoryParams, size: int, salt: int) -> int:
    seed = params.seed
    if seed is None:
        seed = sum(ord(ch) for ch in f"{params.name}|{params.helper}|{params.prop}")
    return random.Random(seed + salt * 104729).randrange(size)


def _words(world: World) -> dict[str, str]:
    c = world.facts["child"]
    p = world.facts["prop"]
    return {
        "name": c.id,
        "prop": p.label,
        "helper": world.facts["helper_phrase"],
        "they": c.pronoun("subject").capitalize(),
        "their": c.pronoun("possessive"),
    }


def flashback(world: World) -> None:
    c = world.facts["child"]
    memory = world.facts["memory"]
    words = _words(world)
    c.meters["confidence"] += 1
    c.memes["hope"] += 1
    lead = {
        "trouble_then_memory": f"The muddle pulled {c.id} into a flashback.",
        "prop_opens_memory": f"As {c.id} checked the {words['prop']}, a flashback arrived before the performance began.",
        "helper_cue": f"From beside the stage, {words['helper']} tapped one finger to one thumb. The tiny signal opened a flashback.",
        "memory_first": f"On the morning of {c.id}'s performance, a quiet moment brought a useful flashback.",
    }[world.facts["params"].scene_order]
    world.say(f"{lead} {memory.memory.format_map(words)}")
    world.say(
        f"Now {c.id} remembered {memory.remembered_skill.format_map(words)}; "
        f"the memory could help {memory.function}."
    )


def start_show(world: World) -> None:
    arc = world.facts["arc"]
    words = _words(world)
    world.say(f"{arc.opening.format_map(words)} At {arc.place}, {arc.audience} watched closely.")


def stumble(world: World) -> None:
    c = world.facts["child"]
    arc = world.facts["arc"]
    words = _words(world)
    c.meters["nervous"] += 1
    c.memes["humor"] += 1
    world.say(arc.disruption.format_map(words))
    form = world.facts["params"].rhyme_form
    if form == "couplets":
        world.say("A wobble can bobble, a clatter can matter; a kind little chuckle is better than chatter.")
    elif form == "refrain":
        world.say(f'"Pause, then play; find a kind way," {c.id} sang, turning the worried hush into a refrain.')
    elif form == "call_response":
        world.say(f'"Is the show all through?" called {c.id}. "Not if we can help you!" the audience rhymed back.')
    else:
        world.say(f"The plan went plink, and one cheek went pink; {c.id} took a small pause and a moment to think.")


def face_moral_choice(world: World) -> None:
    c = world.facts["child"]
    arc = world.facts["arc"]
    moral = world.facts["moral"]
    words = _words(world)
    c.meters["nervous"] -= 1
    c.meters["confidence"] += 1
    c.memes["moral"] += 1
    world.say(f"{arc.cause.format_map(words)} {moral.temptation.format_map(words)}")
    world.say(moral.choice.format_map(words))


def resolve_show(world: World) -> None:
    c = world.facts["child"]
    arc = world.facts["arc"]
    memory = world.facts["memory"]
    words = _words(world)
    method = world.facts["params"].resolution
    bridge = {
        "audience_joins": "The audience supplied a soft clap-clap beat, giving the repair a rhythm instead of a rush.",
        "mistake_becomes_art": f"{c.id} named the mishap 'the surprise verse' and saved one harmless sound or shape from it to use after the real problem was fixed.",
        "quiet_reset": f"For three breaths, {arc.place} became wonderfully still. In that quiet, {c.id} could see the next sensible move.",
        "helper_handoff": f"{words['helper'].capitalize()} kept a soft clap going while {c.id} handled the part of the performance only the performer could do.",
    }[method]
    world.say(
        f"{c.id} used the memory to {memory.function}. "
        f"{bridge} {arc.recovery.format_map(words)}"
    )


def finish(world: World) -> None:
    c = world.facts["child"]
    moral = world.facts["moral"]
    words = _words(world)
    c.meters["joy"] += 2
    c.meters["confidence"] += 1
    endings = [
        f"The applause rose bright, but {c.id} liked the story's moral better: {moral.lesson}.",
        f"That was the moral {c.id} carried home: {moral.lesson}.",
        f"The rhyme had bent without breaking, and its moral was that {moral.lesson}.",
        f"A performance need not be perfect to matter. Its moral was simple: {moral.lesson}.",
    ]
    idx = seeded_index(world.facts["params"], len(endings), 23)
    world.say(endings[idx])
    rhyme_form = world.facts["params"].rhyme_form
    closing_rhyme = {
        "couplets": "The worry took flight in the warm stage light; the ending felt earned, and the lesson felt right.",
        "refrain": 'Once more came the refrain, now merry and bright: "Pause, then play; find a kind way."',
        "call_response": f'"What carried us through?" asked {c.id}. "A brave choice and help!" came the answer anew.',
        "comic_triplet": "The muddle was done. The lesson had won. And nobody needed to hide or run.",
    }[rhyme_form]
    world.say(closing_rhyme)
    world.say(world.facts["ending"].format_map(words))


def tell(params: StoryParams) -> World:
    world = build_world(params)
    order = world.facts["params"].scene_order
    if order in {"prop_opens_memory", "memory_first"}:
        flashback(world)
        world.para()
        start_show(world)
        stumble(world)
    else:
        start_show(world)
        stumble(world)
        world.para()
        flashback(world)
    world.para()
    face_moral_choice(world)
    resolve_show(world)
    world.para()
    finish(world)
    return world


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["child"]
    arc = world.facts["arc"]
    memory = world.facts["memory"]
    moral = world.facts["moral"]
    words = _words(world)
    memory_label = {
        "counting": "counting-beats",
        "kind_mistake": "kind-restart",
        "prop_repair": "repair-practice",
        "honest_promise": "honest-promise",
        "open_space": "open-beat",
    }[memory.key]
    rhyme_label = {
        "couplets": "couplet-style",
        "refrain": "refrain-style",
        "call_response": "call-and-response",
        "comic_triplet": "comic-triplet",
    }[world.facts["params"].rhyme_form]
    resolution_label = {
        "audience_joins": "audience-clapping",
        "mistake_becomes_art": "surprise-verse",
        "quiet_reset": "quiet-reset",
        "helper_handoff": "helper-handoff",
    }[world.facts["params"].resolution]
    return [
        QAItem(
            question=f"In the {moral.value} story with the {resolution_label} resolution, what {rhyme_label} performance was {c.id} giving with the {words['prop']} at {arc.place}?",
            answer=f"{c.id} was giving a {arc.title} at {arc.place}, with the {words['prop']} as a prop."
        ),
        QAItem(
            question=f"What problem did the {memory_label} flashback help {c.id} face on the way to the {resolution_label} resolution and a moral about {moral.value}?",
            answer=arc.disruption.format_map(words)
        ),
        QAItem(
            question=f"How did the {memory_label} flashback help {c.id} reach the {resolution_label} resolution of the {arc.title} while learning about {moral.value}?",
            answer=f"It reminded {c.id} of {memory.remembered_skill.format_map(words)}, helping {memory.function}."
        ),
        QAItem(
            question=f"After the {memory_label} flashback, what moral choice did {c.id} make before the {resolution_label} resolution of the {arc.title}?",
            answer=f"{moral.choice.format_map(words)} This showed {moral.value}."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a performance?",
            answer="A performance is when someone sings, acts, reads, or shows something for other people to watch."
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when the story briefly remembers something that happened before."
        ),
        QAItem(
            question="Why can practice help before a show?",
            answer="Practice helps because it makes the words and moves feel familiar, so they are easier to remember."
        ),
        QAItem(
            question="What is a moral?",
            answer="A moral is the lesson a story teaches, like being kind, brave, or helpful."
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    c = world.facts["child"]
    arc = world.facts["arc"]
    memory = world.facts["memory"]
    moral = world.facts["moral"]
    p = world.facts["prop"]
    return [
        f"Write a child-friendly rhyming story about {c.id}'s {arc.title}, with humor and a useful flashback.",
        f"Tell a performance story where a {p.label} is involved in a real problem and the flashback helps {memory.function}.",
        f"Write a funny, warm story with a concrete ending and a moral about {moral.value}.",
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        out.append(f"{i}. {q}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def asp_facts() -> str:
    import asp
    params = CURATED[0]
    return "\n".join([
        asp.fact("event", "performance"),
        asp.fact("feature", "flashback"),
        asp.fact("feature", "humor"),
        asp.fact("feature", "moral_value"),
        asp.fact("style", "rhyming_story"),
        asp.fact("requires", "practice"),
        asp.fact("helps", "friend"),
    ])


ASP_RULES = r"""
compatible_story(performance, flashback, humor, moral_value, rhyming_story) :-
    event(performance), feature(flashback), feature(humor), feature(moral_value), style(rhyming_story).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible_story/5."))
    ok = bool(asp.atoms(model, "compatible_story"))
    if ok:
        print("OK: ASP gate recognizes the storyworld features.")
        return 0
    print("MISMATCH: ASP gate failed.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small rhyming performance storyworld.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--performance", choices=[arc.key for arc in PERFORMANCES])
    ap.add_argument("--flashback", choices=[path.key for path in FLASHBACKS])
    ap.add_argument("--moral", choices=[path.key for path in MORALS])
    ap.add_argument("--rhyme-form", choices=RHYME_FORMS)
    ap.add_argument("--scene-order", choices=SCENE_ORDERS)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    helper = args.helper or rng.choice(HELPERS)
    prop = args.prop or rng.choice(PROPS)
    return StoryParams(
        name=name,
        gender=gender,
        helper=helper,
        prop=prop,
        performance=args.performance or rng.choice(PERFORMANCES).key,
        flashback=args.flashback or rng.choice(FLASHBACKS).key,
        moral=args.moral or rng.choice(MORALS).key,
        rhyme_form=args.rhyme_form or rng.choice(RHYME_FORMS),
        scene_order=args.scene_order or rng.choice(SCENE_ORDERS),
        resolution=args.resolution or rng.choice(RESOLUTIONS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- trace ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            print(f"{e.id}: meters={meters} memes={memes}")
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(name="Mia", gender="girl", helper="teacher", prop="toy microphone"),
    StoryParams(name="Leo", gender="boy", helper="friend", prop="paper crown"),
    StoryParams(name="Ava", gender="girl", helper="sibling", prop="glittery scarf"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible_story/5."))
        print(asp.atoms(model, "compatible_story"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
