#!/usr/bin/env python3
"""
shiny_cat_sandbox_repetition_curiosity_rhyming_story_2.py
=========================================================

A small StoryWorld for the seed:

    words: shiny cat
    setting: sandbox
    features: Repetition, Curiosity
    style: Rhyming Story

Internal source tale:
    A child is shaping roads and towers in a sandbox when a shiny cat keeps
    repeating one gentle clue over the same patch of sand. The child feels the
    pull to dig fast, but curiosity grows into careful attention instead. By
    matching the clue to the right little search rhyme, the child finds the
    hidden object without wrecking the sandbox. The ending image proves the
    change: the found object now belongs in the open, and the sandbox returns
    from puzzle to play.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample


@dataclass(frozen=True)
class SandboxSite:
    key: str
    phrase: str
    landmark: str
    support_keys: tuple[str, ...]
    sand_texture: str
    end_view: str


@dataclass(frozen=True)
class HiddenThing:
    key: str
    phrase: str
    support_key: str
    hiding_spot: str
    cause: str
    recovery: str
    ending_image: str
    lesson: str


@dataclass(frozen=True)
class SearchRhyme:
    key: str
    phrase: str
    chant: str
    action: str
    tool: str
    solves: tuple[str, ...]


@dataclass
class StoryParams:
    site: str
    hidden_thing: str
    method: str
    hero: str
    gender: str
    helper: str
    seed: int | None = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: dict[str, str] = field(default_factory=dict)

    def add_meter(self, key: str, amount: float) -> None:
        self.meters[key] = round(self.meters.get(key, 0.0) + amount, 2)

    def set_meter(self, key: str, value: float) -> None:
        self.meters[key] = round(value, 2)

    def add_meme(self, key: str, amount: float) -> None:
        self.memes[key] = round(self.memes.get(key, 0.0) + amount, 2)

    def set_tag(self, key: str, value: str) -> None:
        self.tags[key] = value


@dataclass
class World:
    params: StoryParams
    site: SandboxSite
    hidden_thing: HiddenThing
    method: SearchRhyme
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[str] = field(default_factory=list)
    fired_rules: list[str] = field(default_factory=list)
    opening_text: str = ""
    tension_text: str = ""
    turn_text: str = ""
    ending_text: str = ""
    story: str = ""

    def note(self, text: str) -> None:
        self.history.append(text)

    def trace(self) -> str:
        rows = ["--- world model state ---"]
        rows.append(
            f"site={self.site.key} hidden_thing={self.hidden_thing.key} method={self.method.key} "
            f"hero={self.params.hero} helper={helper_name(self.params.helper)}"
        )
        for name, ent in self.entities.items():
            meters = ", ".join(f"{k}={v}" for k, v in sorted(ent.meters.items()))
            memes = ", ".join(f"{k}={v}" for k, v in sorted(ent.memes.items()))
            tags = ", ".join(f"{k}={v}" for k, v in sorted(ent.tags.items()))
            detail = "; ".join(part for part in (meters, memes, tags) if part)
            rows.append(f"  {name:<11} ({ent.kind:<12}) {detail}".rstrip())
        rows.append(f"  fired rules: {self.fired_rules}")
        rows.append("  history:")
        rows.extend(f"    - {item}" for item in self.history)
        return "\n".join(rows)


SITES: dict[str, SandboxSite] = {
    "bucket_step": SandboxSite(
        key="bucket_step",
        phrase="the bucket step near the tallest tower",
        landmark="three bright buckets stacked beside a crumbly road",
        support_keys=("gleam", "trail"),
        sand_texture="sun-warm sand with a smooth top crust",
        end_view="the bucket step sat smooth again beside the tallest tower",
    ),
    "moat_curve": SandboxSite(
        key="moat_curve",
        phrase="the bend of the little moat",
        landmark="a curving moat circling a sand castle gate",
        support_keys=("slide", "gleam"),
        sand_texture="damp sand that held soft rings",
        end_view="the moat curve lay still beside the castle gate",
    ),
    "tunnel_shade": SandboxSite(
        key="tunnel_shade",
        phrase="the shady tunnel side of the sandbox",
        landmark="a cool arch cut through a mound of sand",
        support_keys=("jingle", "trail"),
        sand_texture="cool sand tucked under a hollow arch",
        end_view="the tunnel shade looked neat again under the little arch",
    ),
    "castle_door": SandboxSite(
        key="castle_door",
        phrase="the tiny castle door at the front wall",
        landmark="a thumb-made doorway with shell steps",
        support_keys=("jingle", "slide"),
        sand_texture="packed sand with a narrow seam by the shell steps",
        end_view="the castle door stood proud with clean shell steps below",
    ),
}


HIDDEN_THINGS: dict[str, HiddenThing] = {
    "sun_button": HiddenThing(
        key="sun_button",
        phrase="a round sun button",
        support_key="gleam",
        hiding_spot="beneath a thin lid of bright dry sand",
        cause="a shiny yellow button kept catching one quick wink of light whenever the sun brushed the top layer",
        recovery="brushed away the dry grains with a pail lid until the little button shone free",
        ending_image="The sun button gleamed on the sand castle gate, bright and light in the late-day light.",
        lesson="Curiosity can be bright without being rough when small clues ask for careful eyes.",
    ),
    "shell_bell": HiddenThing(
        key="shell_bell",
        phrase="a tiny shell bell",
        support_key="jingle",
        hiding_spot="inside a snug sandy pocket below the crust",
        cause="a tiny shell bell hid in a sandy pocket and gave a soft jingle each time a paw tapped the crust above it",
        recovery="held still, listened low, and lifted the bell from its sandy pocket without crumbling the sand wall",
        ending_image="The shell bell rested on a sandy ledge, and its tiny ring turned into a happy sing.",
        lesson="Curiosity grows wiser when it listens before it lunges.",
    ),
    "moon_key": HiddenThing(
        key="moon_key",
        phrase="a moon-shaped toy key",
        support_key="trail",
        hiding_spot="under a loop of neat paw marks",
        cause="the shiny cat kept walking the same tiny ring because a moon-shaped key lay just under the coolest patch",
        recovery="followed the paw loop, pressed the sand, and lifted the toy key from the marked circle",
        ending_image="The moon key swung from the bucket handle, ready and steady as the shadows grew blue.",
        lesson="Repeating tracks become a map when a child stays curious long enough to read them.",
    ),
    "silver_spoon": HiddenThing(
        key="silver_spoon",
        phrase="a little silver spoon",
        support_key="slide",
        hiding_spot="just below a damp slipping seam",
        cause="a little silver spoon made the damp sand slide back to the same line whenever the cat patted nearby",
        recovery="smoothed the damp seam in slow strokes until the spoon edge slipped into view",
        ending_image="The silver spoon rested beside the smooth seam, and the last small drip went still instead of spill.",
        lesson="Gentle curiosity can read moving sand better than hurry can.",
    ),
}


METHODS: dict[str, SearchRhyme] = {
    "brush_brush_bright": SearchRhyme(
        key="brush_brush_bright",
        phrase="a brush-brush-bright search",
        chant="Brush, brush, bright; little clue, show your light.",
        action="swept the top grains in tiny moons with a pail lid",
        tool="a pail lid",
        solves=("gleam",),
    ),
    "listen_listen_ring": SearchRhyme(
        key="listen_listen_ring",
        phrase="a listen-listen-ring search",
        chant="Listen, listen, ring; soft clues love to sing.",
        action="held still, hummed once, and listened under the sandy crust",
        tool="quiet ears",
        solves=("jingle",),
    ),
    "follow_follow_find": SearchRhyme(
        key="follow_follow_find",
        phrase="a follow-follow-find search",
        chant="Follow, follow, find; gentle tracks can guide the mind.",
        action="followed the repeated paw loop and pressed the center with flat fingers",
        tool="flat fingers",
        solves=("trail",),
    ),
    "smooth_smooth_slow": SearchRhyme(
        key="smooth_smooth_slow",
        phrase="a smooth-smooth-slow search",
        chant="Smooth, smooth, slow; hidden things will show.",
        action="smoothed the damp seam in patient strokes and watched where the sand slipped back",
        tool="patient fingertips",
        solves=("slide",),
    ),
}


HERO_NAMES: dict[str, tuple[str, ...]] = {
    "girl": ("Lila", "Mina", "Tess"),
    "boy": ("Nico", "Owen", "Rafi"),
}


HELPERS: dict[str, str] = {
    "aunt_bea": "Aunt Bea",
    "dad": "Dad",
    "teacher_jo": "Teacher Jo",
}


CAT_NAME = "Twinkle"


def helper_name(key: str) -> str:
    return HELPERS[key]


def valid_combo(site: str, hidden_thing: str, method: str) -> bool:
    if site not in SITES or hidden_thing not in HIDDEN_THINGS or method not in METHODS:
        return False
    need = HIDDEN_THINGS[hidden_thing].support_key
    return need in SITES[site].support_keys and need in METHODS[method].solves


def explain_rejection(site: str, hidden_thing: str, method: str) -> str:
    if site not in SITES:
        return f"No story: unknown sandbox site {site!r}."
    if hidden_thing not in HIDDEN_THINGS:
        return f"No story: unknown hidden sandbox object {hidden_thing!r}."
    if method not in METHODS:
        return f"No story: unknown search rhyme {method!r}."
    need = HIDDEN_THINGS[hidden_thing].support_key
    if need not in SITES[site].support_keys:
        return (
            f"No story: {SITES[site].phrase} cannot reasonably hide {HIDDEN_THINGS[hidden_thing].phrase}; "
            f"that object needs a {need} clue."
        )
    if need not in METHODS[method].solves:
        return (
            f"No story: {METHODS[method].phrase} does not fit {HIDDEN_THINGS[hidden_thing].phrase}; "
            f"that clue calls for a {need} search."
        )
    return "No story: the sandbox choices do not form a grounded rhyme tale."


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for site in sorted(SITES):
        for hidden_thing in sorted(HIDDEN_THINGS):
            for method in sorted(METHODS):
                if valid_combo(site, hidden_thing, method):
                    combos.append((site, hidden_thing, method))
    return combos


def _pick_hero(rng: random.Random, gender: str) -> str:
    return rng.choice(HERO_NAMES[gender])


def build_world(params: StoryParams) -> World:
    site = SITES[params.site]
    hidden_thing = HIDDEN_THINGS[params.hidden_thing]
    method = METHODS[params.method]
    hero = Entity(name=params.hero, kind="child")
    cat = Entity(name=CAT_NAME, kind="cat")
    sandbox = Entity(name="Sandbox", kind="place")
    object_ent = Entity(name=hidden_thing.phrase, kind="hidden_object")
    helper = Entity(name=helper_name(params.helper), kind="helper")
    world = World(
        params=params,
        site=site,
        hidden_thing=hidden_thing,
        method=method,
        entities={
            "Hero": hero,
            "Cat": cat,
            "Sandbox": sandbox,
            "Hidden": object_ent,
            "Helper": helper,
        },
    )
    sandbox.set_tag("landmark", site.landmark)
    sandbox.set_tag("sand_texture", site.sand_texture)
    sandbox.set_meter("smoothness", 1.0)
    sandbox.set_meter("disturbed", 0.0)
    object_ent.set_tag("spot", hidden_thing.hiding_spot)
    object_ent.set_meter("found", 0.0)
    return world


def _r_open_sandbox_song(world: World) -> bool:
    hero = world.entities["Hero"]
    cat = world.entities["Cat"]
    sandbox = world.entities["Sandbox"]

    hero.add_meme("curiosity", 0.8)
    hero.add_meme("play", 0.9)
    hero.add_meter("hurry", 0.2)
    hero.add_meter("search_loops", 0.0)
    cat.add_meme("focus", 1.0)
    cat.add_meme("wonder", 0.8)
    sandbox.add_meme("play", 1.0)
    sandbox.add_meme("mystery", 0.5)

    world.opening_text = (
        f"In the sandbox, soft and bright, {world.params.hero} built with morning light. "
        f"By {world.site.phrase} padded a shiny cat named {CAT_NAME}, sleek as a penny and quick as a kite. "
        f"Near {world.site.landmark}, the sand looked ordinary, but {CAT_NAME} kept giving one patch a thoughtful stare."
    )
    world.note(
        f"{world.params.hero} played at {world.site.phrase} while {CAT_NAME} watched one patch of sand near {world.site.landmark}."
    )
    return True


def _r_repeat_the_clue(world: World) -> bool:
    hero = world.entities["Hero"]
    cat = world.entities["Cat"]
    hidden = world.entities["Hidden"]
    sandbox = world.entities["Sandbox"]

    hero.add_meme("curiosity", 0.9)
    hero.add_meter("hurry", 0.7)
    cat.set_meter("repeat_count", 3.0)
    cat.add_meter("steps", 3.0)
    hidden.set_tag("cause", world.hidden_thing.cause)
    sandbox.add_meme("mystery", 0.7)

    if world.hidden_thing.support_key == "gleam":
        repeat_action = "blink, blink, bow"
        repeat_reason = "a hidden bright button was winking under the top layer"
        clue = (
            f"Three times {CAT_NAME} blinked and bowed at the same sandy speck, and three times a tiny wink of light answered back."
        )
    elif world.hidden_thing.support_key == "jingle":
        repeat_action = "tap, pause, listen"
        repeat_reason = "a buried shell bell kept answering each soft tap"
        clue = (
            f"Three times {CAT_NAME} tapped the crust, paused, and listened, and three times a little jingle hid below the hush."
        )
    elif world.hidden_thing.support_key == "trail":
        repeat_action = "step, step, circle"
        repeat_reason = "a moon-shaped key lay just under the coolest patch"
        clue = (
            f"Three times {CAT_NAME} walked the same neat ring, step by step, until a paw-loop circled one small patch like a string."
        )
    else:
        repeat_action = "pat, smooth, wait"
        repeat_reason = "a little silver spoon kept making the damp seam slip back"
        clue = (
            f"Three times {CAT_NAME} patted the damp seam, and three times the same narrow slip slid softly back into line."
        )

    cat.set_tag("repeat_action", repeat_action)
    hidden.set_tag("repeat_reason", repeat_reason)
    world.tension_text = (
        f"{clue} {world.params.hero} almost scooped the whole spot apart in a sandy rush, "
        f"but curiosity rose higher than hurry and made the child stop and hush."
    )
    world.note(
        f"{CAT_NAME} repeated {repeat_action} three times because {world.hidden_thing.cause}"
    )
    return True


def _r_curiosity_chooses_care(world: World) -> bool:
    hero = world.entities["Hero"]
    helper = world.entities["Helper"]
    sandbox = world.entities["Sandbox"]

    curiosity = hero.memes.get("curiosity", 0.0)
    hurry = hero.meters.get("hurry", 0.0)
    if curiosity <= hurry:
        raise StoryError(
            "No story: the child's hurry overpowers curiosity, so the sandbox search would turn destructive."
        )

    hero.add_meme("care", 1.0)
    hero.add_meme("confidence", 0.8)
    hero.add_meter("search_loops", 3.0)
    sandbox.set_meter("disturbed", 0.2)
    helper.add_meme("approval", 0.6)
    helper.set_tag("advice", "Small clues like small hands.")

    world.turn_text = (
        f"\"{world.method.chant}\" {world.params.hero} sang once, then twice, then thrice, "
        f"using {world.method.phrase} and {world.method.action}. "
        f"That was the turn: {world.hidden_thing.cause}, so the careful rhyme fit the clue instead of fighting it."
    )
    world.note(
        f"{world.params.hero} chose {world.method.phrase} because curiosity stayed stronger than hurry."
    )
    return True


def _r_find_and_restore(world: World) -> bool:
    hero = world.entities["Hero"]
    cat = world.entities["Cat"]
    hidden = world.entities["Hidden"]
    sandbox = world.entities["Sandbox"]
    helper = world.entities["Helper"]

    hero.add_meme("joy", 1.0)
    hero.add_meme("relief", 0.9)
    cat.add_meme("calm", 1.0)
    sandbox.add_meme("mystery", -0.8)
    sandbox.add_meme("play", 0.4)
    sandbox.set_meter("smoothness", 0.95)
    hidden.set_meter("found", 1.0)
    hidden.set_tag("recovery", world.hidden_thing.recovery)
    hidden.set_tag("ending_image", world.hidden_thing.ending_image)
    hidden.set_tag("resolved", "yes")
    helper.set_tag("saw_result", "yes")

    world.ending_text = (
        f"{world.params.hero} {world.hidden_thing.recovery}. "
        f"{helper.name} smiled and said that calm curiosity had been the smartest tool of all. "
        f"{world.hidden_thing.ending_image} Nearby, {CAT_NAME} curled its tail while {world.site.end_view}, "
        f"and the sandbox felt less like a riddle and more like a little rhyme."
    )
    world.note(
        f"{world.hidden_thing.phrase} was found at {world.hidden_thing.hiding_spot}, and the sandbox returned to play."
    )
    return True


RULES: tuple[tuple[str, Callable[[World], bool]], ...] = (
    ("open_sandbox_song", _r_open_sandbox_song),
    ("repeat_the_clue", _r_repeat_the_clue),
    ("curiosity_chooses_care", _r_curiosity_chooses_care),
    ("find_and_restore", _r_find_and_restore),
)


def run_world(world: World) -> World:
    for name, rule in RULES:
        if rule(world):
            world.fired_rules.append(name)
    return world


def render_story(world: World) -> str:
    paragraph_two = (
        f"{world.tension_text} So instead of throwing sand high in the sky, "
        f"{world.params.hero} decided to try a patient reply."
    )
    paragraph_three = f"{world.turn_text} {world.ending_text} {world.hidden_thing.lesson}"
    return "\n\n".join((world.opening_text, paragraph_two, paragraph_three))


def prompts_for(world: World) -> list[str]:
    cat = world.entities["Cat"]
    return [
        f"Tell a child-friendly rhyming story set in a sandbox about {world.params.hero} and a shiny cat named {CAT_NAME}.",
        f"Use repetition by having the cat repeat {cat.tags['repeat_action']} three times at {world.site.phrase}.",
        f"Let curiosity guide {world.params.hero} to use {world.method.phrase} and end with {world.hidden_thing.ending_image}",
    ]


def story_qa_for(world: World) -> list[QAItem]:
    hero = world.entities["Hero"]
    cat = world.entities["Cat"]
    hidden = world.entities["Hidden"]
    helper = world.entities["Helper"]
    return [
        QAItem(
            question="Why did the child stop and pay attention to one patch of sand?",
            answer=(
                f"{CAT_NAME}, the shiny cat, repeated the same clue three times at {world.site.phrase}. "
                f"That repetition made {world.params.hero} think the sand was pointing to a real hidden object instead of asking for random digging."
            ),
        ),
        QAItem(
            question="What problem almost spoiled the search in the middle of the story?",
            answer=(
                f"{world.params.hero} nearly scooped the whole place apart in a hurry. "
                f"The problem changed when curiosity rose higher than hurry and turned the search toward care instead of mess."
            ),
        ),
        QAItem(
            question="How did the child search once curiosity took the lead?",
            answer=(
                f"{world.params.hero} used {world.method.phrase} and repeated the chant, \"{world.method.chant}\" three times. "
                f"That method matched the clue kind, so the child could search the right spot without wrecking the sandbox."
            ),
        ),
        QAItem(
            question="What was hidden under the sand, and why was the shiny cat repeating itself?",
            answer=(
                f"The hidden object was {world.hidden_thing.phrase}, tucked {world.hidden_thing.hiding_spot}. "
                f"{CAT_NAME} kept repeating its little pattern because {hidden.tags['repeat_reason']}."
            ),
        ),
        QAItem(
            question="Who noticed that careful curiosity had worked, and what did they see at the end?",
            answer=(
                f"{helper.name} saw the result and praised the calm search. "
                f"The proof was this ending image: {hidden.tags['ending_image']}"
            ),
        ),
    ]


def world_qa_for(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why can repetition help someone solve a small sandbox mystery?",
            answer=(
                "Repetition marks the detail that keeps mattering, so a child does not have to treat every grain of sand as equally important. "
                "When the same clue returns again and again, it becomes a map instead of a blur."
            ),
        ),
        QAItem(
            question="Why is curiosity better than hurry when something tiny is buried in sand?",
            answer=(
                "Curiosity asks what the clue means before the hands start scooping everywhere. "
                "That protects the shape of the sand and keeps the hidden object's own clue from being rubbed away."
            ),
        ),
        QAItem(
            question="Why should a search method fit the kind of clue?",
            answer=(
                "Different clues need different kinds of attention, such as listening for a bell or smoothing a slipping seam. "
                "A matched method uses the world as it is, which makes the answer easier to uncover and the setting easier to preserve."
            ),
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params.site, params.hidden_thing, params.method):
        raise StoryError(explain_rejection(params.site, params.hidden_thing, params.method))
    world = run_world(build_world(params))
    story = render_story(world)
    world.story = story
    return StorySample(
        params=params,
        story=story,
        prompts=prompts_for(world),
        story_qa=story_qa_for(world),
        world_qa=world_qa_for(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Prompts ==", *[f"{i}. {item}" for i, item in enumerate(sample.prompts, 1)], ""]
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
    parser = argparse.ArgumentParser(description="Sandbox shiny-cat repetition curiosity rhyming world.")
    parser.add_argument("--site", choices=sorted(SITES))
    parser.add_argument("--hidden-thing", dest="hidden_thing", choices=sorted(HIDDEN_THINGS))
    parser.add_argument("--method", choices=sorted(METHODS))
    parser.add_argument("--hero")
    parser.add_argument("--gender", choices=sorted(HERO_NAMES))
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
        if (args.site is None or combo[0] == args.site)
        and (args.hidden_thing is None or combo[1] == args.hidden_thing)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError(
            explain_rejection(
                args.site or "bucket_step",
                args.hidden_thing or "sun_button",
                args.method or "brush_brush_bright",
            )
        )
    site, hidden_thing, method = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(sorted(HERO_NAMES))
    hero = args.hero or _pick_hero(rng, gender)
    helper = args.helper or rng.choice(sorted(HELPERS))
    return StoryParams(
        site=site,
        hidden_thing=hidden_thing,
        method=method,
        hero=hero,
        gender=gender,
        helper=helper,
    )


ASP_RULES = r"""
combo(S,H,M) :-
  site(S), hidden_thing(H), method(M),
  site_support(S,N), hidden_need(H,N), method_solves(M,N).

#show combo/3.
"""


def asp_facts() -> str:
    from storyworlds import asp

    rows: list[str] = []
    for site in SITES.values():
        rows.append(asp.fact("site", site.key))
        for support in site.support_keys:
            rows.append(asp.fact("site_support", site.key, support))
    for hidden_thing in HIDDEN_THINGS.values():
        rows.append(asp.fact("hidden_thing", hidden_thing.key))
        rows.append(asp.fact("hidden_need", hidden_thing.key, hidden_thing.support_key))
    for method in METHODS.values():
        rows.append(asp.fact("method", method.key))
        for support in method.solves:
            rows.append(asp.fact("method_solves", method.key, support))
    return "\n".join(rows)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    from storyworlds import asp

    model = asp.one_model(asp_program("#show combo/3."))
    return sorted(set(asp.atoms(model, "combo")))


def exercise_generated_stories() -> list[str]:
    problems: list[str] = []
    for i, combo in enumerate(valid_combos()):
        params = StoryParams(
            site=combo[0],
            hidden_thing=combo[1],
            method=combo[2],
            hero="Lila",
            gender="girl",
            helper="aunt_bea",
            seed=2400 + i,
        )
        sample = generate(params)
        story_lower = sample.story.lower()
        world = sample.world
        if "shiny cat" not in story_lower:
            problems.append(f"{combo}: story is missing the seed phrase 'shiny cat'")
        if "sandbox" not in story_lower:
            problems.append(f"{combo}: story is missing the sandbox setting")
        if sample.story.count("\n\n") < 2:
            problems.append(f"{combo}: story is missing a clear beginning, middle, or ending paragraph")
        if METHODS[combo[2]].chant not in sample.story:
            problems.append(f"{combo}: story does not render the search chant")
        if len(sample.story_qa) < 5:
            problems.append(f"{combo}: story-grounded QA set is too small")
        if len(sample.world_qa) < 3:
            problems.append(f"{combo}: world-knowledge QA set is too small")
        if any(item.answer.count(".") < 2 for item in sample.story_qa):
            problems.append(f"{combo}: a story-grounded QA answer is too short")
        if "{" in sample.story or "}" in sample.story:
            problems.append(f"{combo}: story leaked unresolved template markers")
        if "  " in sample.story:
            problems.append(f"{combo}: story contains doubled spaces")
        if world is None:
            problems.append(f"{combo}: sample is missing its world model")
            continue
        hero = world.entities["Hero"]
        if world.entities["Cat"].meters.get("repeat_count") != 3.0:
            problems.append(f"{combo}: repetition state was not recorded in the cat entity")
        if hero.memes.get("curiosity", 0.0) <= hero.meters.get("hurry", 0.0):
            problems.append(f"{combo}: curiosity never overcame hurry in the hero state")
        if world.entities["Hidden"].meters.get("found") != 1.0:
            problems.append(f"{combo}: hidden object was never marked as found")
        if world.entities["Hidden"].tags.get("resolved") != "yes":
            problems.append(f"{combo}: hidden object never reached a resolved state")
        if world.entities["Sandbox"].meters.get("disturbed", 1.0) > 0.3:
            problems.append(f"{combo}: sandbox was disturbed too much for a gentle solution")
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
        print("OK: generated stories pass seed, structure, QA, repetition, curiosity, and resolution checks.")
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
        raise StoryError("Not enough unique sandbox stories from the current constraints.")
    return samples


def _sample_all(args: argparse.Namespace) -> list[StorySample]:
    rows: list[StorySample] = []
    base_seed = args.seed if args.seed is not None else 19
    for i, combo in enumerate(valid_combos()):
        params = StoryParams(
            site=combo[0],
            hidden_thing=combo[1],
            method=combo[2],
            hero="Lila",
            gender="girl",
            helper="aunt_bea",
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
