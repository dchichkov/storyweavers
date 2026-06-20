#!/usr/bin/env python3
"""sesame_repetition_curiosity_rhyming_story.py
=================================================

A short StoryWorld built from this source tale:

A child finds a missing jar labeled "sesame" and the clue seems to be a repeated
rhyming line. Instead of guessing wildly, the child keeps repeating the sesame
line, notices where the same pattern points, picks a physical tool, and then
opens the jar carefully. Curiosity stays calm, and the ending shows the jar
open with seeds ready for baking.

Words: sesame
Features: Repetition, Curiosity
Style: Rhyming Story
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

from results import QAItem, StoryError, StorySample


@dataclass(frozen=True)
class HidingPlace:
    key: str
    label: str
    lock: str
    hide_spot: str
    obstacle: str
    start_line: str
    end_view: str


@dataclass(frozen=True)
class SesameClue:
    key: str
    line: str
    place: str
    misread: str


@dataclass(frozen=True)
class OpenTool:
    key: str
    label: str
    solves: str
    action: str
    reason: str


@dataclass(frozen=True)
class StoryParams:
    place: str
    clue: str
    tool: str
    seed: int | None = None


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    props: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Event:
    id: str
    text: str
    actor: str
    target: str | None = None


@dataclass
class SesameWorld:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, str | int | float | bool] = field(default_factory=dict)
    rng: random.Random | None = None

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def record(self, event_id: str, text: str, actor: str, target: str | None = None) -> None:
        self.history.append(Event(event_id, text, actor, target))
        self.say(text)

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


PLACES: dict[str, HidingPlace] = {
    "attic": HidingPlace(
        key="attic",
        label="the old attic beam",
        lock="cord_knot",
        hide_spot="caught in a looped ribbon above the flour sacks",
        obstacle="A silk ribbon looped the jar handle and snagged on a hidden beam hook.",
        start_line="the attic held its breath, and every string seemed to hum in surprise.",
        end_view="the jar sat safely on the counter, open, with sesame seeds shining like tiny beads of sunrise.",
    ),
    "pantry": HidingPlace(
        key="pantry",
        label="the cool pantry shelf",
        lock="wax_seal",
        hide_spot="wedged under a small metal pan where a wax line clung to the edge.",
        obstacle="The jar lid had sealed with warm wax, holding shut like a stubborn note.",
        start_line="the pantry kept its hush, then released a little waxy glow under the light.",
        end_view="the jar rolled out with a clean pop, and the sesame seeds fell into a bowl like rain on a drumskin.",
    ),
    "shed": HidingPlace(
        key="shed",
        label="the garden shed floor",
        lock="mud_edge",
        hide_spot="stuck in the wet mud seam beside the watering tub rim.",
        obstacle="A thin mud seam pinned the jar against the floor edge like a quiet latch.",
        start_line="the shed smelled of earth and rain, and the mud had a story all by itself.",
        end_view="the jar rose clear, and sesame seeds glittered on a blue cloth like stars after rain.",
    ),
}

CLUES: dict[str, SesameClue] = {
    "dust_ring": SesameClue(
        key="dust_ring",
        line="Sesame, sesame, dust in a ring, point me to the place where ribbons sing.",
        place="attic",
        misread="The line sounded playful, and the child first thought it was just a silly kitchen rhyme.",
    ),
    "quiet_fan": SesameClue(
        key="quiet_fan",
        line="Sesame, sesame, hush in the air, follow the place where silks drift there.",
        place="attic",
        misread="The rhyme was short and bouncy, and it felt like a game instead of a clue.",
    ),
    "warm_glow": SesameClue(
        key="warm_glow",
        line="Sesame, sesame, where warm wax gleams, show the jar the door to secret dreams.",
        place="pantry",
        misread="Piper thought the rhyme meant someone had polished the pantry for decoration.",
    ),
    "sweet_ribbon": SesameClue(
        key="sweet_ribbon",
        line="Sesame, sesame, sugar and song, point to where the wax went wrong.",
        place="pantry",
        misread="The line sounded like dessert counting, so fear of missing out replaced calm.",
    ),
    "mud_drip": SesameClue(
        key="mud_drip",
        line="Sesame, sesame, mud and tide, where the jar had slipped and then had to hide.",
        place="shed",
        misread="Piper briefly thought someone must have made a joke about mud-cups.",
    ),
    "wheel_murmur": SesameClue(
        key="wheel_murmur",
        line="Sesame, sesame, wheel and wheel, tell the truth about what is real.",
        place="shed",
        misread="The rhyme felt mysterious enough to be a trick, not a direction.",
    ),
}

TOOLS: dict[str, OpenTool] = {
    "cord_cutter": OpenTool(
        key="cord_cutter",
        label="a tiny cord cutter",
        solves="cord_knot",
        action="Lila uncoiled the cord and slipped the cutter under the ribbon knot, then released the jar gently.",
        reason="The cord knot only gives way to a thin, patient release, not force.",
    ),
    "loop_hook": OpenTool(
        key="loop_hook",
        label="a loop hook",
        solves="cord_knot",
        action="She used the loop hook to lift and untangle the tied ribbon from the beam hook, then eased the jar free.",
        reason="A looped knot can be lifted with leverage, which the loop hook provides.",
    ),
    "wax_pal": OpenTool(
        key="wax_pal",
        label="a warm wet cloth",
        solves="wax_seal",
        action="Piper warmed a clean cloth and laid it along the wax line until it softened and slipped away from the lid.",
        reason="Wax softens with gentle heat, making the lid open without cracking it.",
    ),
    "scoop_knife": OpenTool(
        key="scoop_knife",
        label="a short scoop knife",
        solves="wax_seal",
        action="Piper worked the scoop knife flat along the wax edge, lifting just the seal instead of prying the lid itself.",
        reason="A flat edge lifts softened wax while preserving the jar and the sesame seeds inside.",
    ),
    "mud_hook": OpenTool(
        key="mud_hook",
        label="a mud hook",
        solves="mud_edge",
        action="Lila hooked the jar edge and raised it from the wet seam without dragging it through the grit.",
        reason="A hook reaches under a mud-locked edge where hands would push the jar deeper.",
    ),
    "root_spatula": OpenTool(
        key="root_spatula",
        label="a short farm spatula",
        solves="mud_edge",
        action="With a spatula, Piper lifted the mud lip first and slid the jar out in one smooth turn.",
        reason="A flat scoop creates space at the seam so the jar can turn free cleanly.",
    ),
}


OPENING_IMAGES = (
    "The streetlight stripe on the bakery window looked like a silver ribbon.",
    "Steam curled from the sink like a tiny gray ponytail.",
)

TURN_IMAGES = (
    "The repeated lines made the fear calm down and the room feel more like a puzzle.",
    "The room stayed still, and the repeated phrase made the path feel less loud and more clear.",
)


def valid_params(params: StoryParams) -> tuple[bool, str]:
    if params.place not in PLACES:
        return False, f"unknown place: {params.place}"
    if params.clue not in CLUES:
        return False, f"unknown clue: {params.clue}"
    if params.tool not in TOOLS:
        return False, f"unknown tool: {params.tool}"
    place = PLACES[params.place]
    clue = CLUES[params.clue]
    tool = TOOLS[params.tool]
    if clue.place != params.place:
        return False, "the selected clue points to a different place"
    if tool.solves != place.lock:
        return False, "the selected tool does not match this place's obstruction"
    return True, ""


def explain_invalid(place: str | None, clue: str | None, tool: str | None) -> str:
    if place is not None and place not in PLACES:
        return f"No story: unknown place {place!r}."
    if clue is not None and clue not in CLUES:
        return f"No story: unknown clue {clue!r}."
    if tool is not None and tool not in TOOLS:
        return f"No story: unknown tool {tool!r}."
    if place and clue and (clue not in CLUES or CLUES[clue].place != place):
        return "No story: the chosen clue points to a different place."
    if place and tool and (tool not in TOOLS or TOOLS[tool].solves != PLACES[place].lock):
        return "No story: the chosen tool cannot loosen the obstruction at the chosen place."
    return "No story: that parameter mix is not supported by the current recipe."


def all_params() -> list[StoryParams]:
    items: list[StoryParams] = []
    for place in sorted(PLACES):
        for clue in sorted(CLUES):
            for tool in sorted(TOOLS):
                params = StoryParams(place=place, clue=clue, tool=tool)
                if valid_params(params)[0]:
                    items.append(params)
    return items


def make_world(params: StoryParams) -> SesameWorld:
    place = PLACES[params.place]
    clue = CLUES[params.clue]
    tool = TOOLS[params.tool]
    rng = random.Random(params.seed or 0)

    world = SesameWorld(params=params, rng=rng)
    world.add(Entity(id="lila", kind="character", type="girl", label="Lila", traits=["curious", "careful"]))
    world.add(Entity(id="piper", kind="character", type="boy", label="Piper", traits=["kind", "steady"]))
    world.add(Entity(id="bakery", kind="place", type="kitchen", label="Grandma Lane Bakery"))
    world.add(Entity(id="attic", kind="place", type="attic", label="the old attic beam"))
    world.add(Entity(id="pantry", kind="place", type="pantry", label="the cool pantry shelf"))
    world.add(Entity(id="shed", kind="place", type="shed", label="the garden shed floor"))
    world.add(Entity(id="jar", kind="object", type="seed_jar", label="the sesame jar"))
    world.add(Entity(id="seeds", kind="object", type="seed", label="sesame seeds"))

    home = world.get("bakery")
    lila = world.get("lila")
    piper = world.get("piper")
    jar = world.get("jar")
    seeds = world.get("seeds")
    location = world.get(params.place)

    home.meters["quiet"] = 1.0
    location.meters["attention"] = 1.0
    jar.meters["present"] = 1.0
    jar.meters["hidden"] = 0.0
    jar.meters["open"] = 0.0
    jar.meters["obstructed"] = 1.0
    seeds.meters["stored"] = 1.0

    lila.memes["curiosity"] = 1.0
    piper.memes["curiosity"] = 0.8
    lila.memes["trust"] = 1.5

    world.facts.update(
        place=params.place,
        chosen_place_label=place.label,
        chosen_clue_line=clue.line,
        chosen_tool=tool.label,
        obstacle=place.obstacle,
        misread=clue.misread,
        opening_image=rng.choice(OPENING_IMAGES),
        turn_image=rng.choice(TURN_IMAGES),
        ending_image=place.end_view,
    )

    return world


def opening(world: SesameWorld) -> None:
    jar = world.get("jar")
    lila = world.get("lila")
    piper = world.get("piper")
    place = PLACES[world.params.place]

    jar.meters["hidden"] += 0.0
    lila.memes["joy"] += 1.0
    piper.memes["joy"] += 0.7

    world.record(
        "opening",
        f"Sunday morning rang with small clinks, and the bakery wore a sleepy gold light. {world.facts['opening_image']} "
        f"Lila and Piper promised to bake sesame biscuits for their neighbor's fair, and the word to remember was the same every time: sesame.",
        "lila",
    )
    world.record(
        "motivation",
        f"They set the sesame jar in the middle of the counter so it could lead the recipe steps, then listened to the old note pinned by the flour. The note kept repeating in a rhyme, and {place.start_line}",
        "lila",
        target="jar",
    )


def jar_disappears(world: SesameWorld) -> None:
    place = PLACES[world.params.place]
    jar = world.get("jar")
    lila = world.get("lila")
    piper = world.get("piper")

    jar.meters["present"] = 0.0
    jar.meters["hidden"] = 1.0
    jar.meters["in_motion"] = 1.0
    lila.memes["worry"] += 1.0
    piper.memes["worry"] += 0.9

    world.record(
        "loss",
        f"Then the jar gave a tiny wobble, rolled through a gap in the counter edge, and vanished toward {place.label}."
        f"It was still there somewhere, but not where the recipe expected it, and suddenly their bright morning felt a little tense.",
        "piper",
        target="jar",
    )


def repeat_and_reason(world: SesameWorld) -> None:
    clue = CLUES[world.params.clue]
    lila = world.get("lila")
    piper = world.get("piper")

    repetition = 0
    for turn in range(1, 4):
        repetition += 1
        if turn == 1:
            text = (
                f"Lila sang the line once: \"{clue.line}\" and looked hard at the shelf. "
                f"Her first read made no sense yet; she only heard a bright sound and felt a little unsure. "
                f"{clue.misread}"
            )
            lila.memes["confusion"] += 0.6
        elif turn == 2:
            world.para()
            text = (
                f"She sang again, and the line came back a bit clearer: \"{clue.line}\". "
                f"Piper matched the pace to a steady stamp: one, two, three. "
                f"{world.facts['turn_image']}"
            )
            lila.memes["patience"] += 0.5
            piper.memes["focus"] += 0.8
        else:
            place = PLACES[world.params.place]
            text = (
                f"On the third try, they sang together and the pattern snapped into place. "
                f"The words had been pointing all along to {place.label}, where a small clue lay true: {place.obstacle} "
                f"and the jar was hidden {place.hide_spot}."
            )
            lila.memes["focus"] += 1.0
            piper.memes["focus"] += 0.6
    world.facts["repetitions"] = repetition
    world.record("repetition", text, "lila")

    world.facts["found_place"] = world.params.place


def use_tool(world: SesameWorld) -> None:
    jar = world.get("jar")
    lila = world.get("lila")
    piper = world.get("piper")
    place = PLACES[world.params.place]
    tool = TOOLS[world.params.tool]

    jar.meters["open"] = 1.0
    jar.meters["hidden"] = 0.0
    jar.meters["obstructed"] = 0.0
    jar.meters["present"] = 1.0
    jar.props["opened_by"] = tool.key
    lila.memes["confidence"] += 1.2
    piper.memes["confidence"] += 1.0

    world.record(
        "tool",
        f"The final turn matched the clue and the lock. {tool.action} {tool.reason} "
        f"That choice made the search feel like a riddle finally solved, not a guess.",
        "piper",
        target="jar",
    )

    world.record(
        "resolve",
        f"As the jar came free, sesame seeds rained into a bowl in a tiny silver stream. "
        f"The obstruction was gone, and the sesame answer had become a visible change in the room.",
        "lila",
        target="seeds",
    )


def close_story(world: SesameWorld) -> None:
    lila = world.get("lila")
    piper = world.get("piper")
    jar = world.get("jar")
    seeds = world.get("seeds")

    jar.meters["open"] = 1.0
    seeds.meters["stored"] = 0.0
    seeds.meters["ready_for_bake"] = 1.0

    lila.memes["joy"] += 1.3
    piper.memes["joy"] += 1.3
    lila.memes["trust"] += 1.0
    piper.memes["trust"] += 1.0
    world.facts["resolved"] = True

    world.record(
        "ending",
        f"Back at the counter, {world.facts['ending_image']} The room felt complete, "
        f"and both children smiled. Sesame rhyme had made them patient, and curiosity kept their hands gentle until the truth could be seen.",
        "lila",
        target="jar",
    )


def tell(params: StoryParams) -> SesameWorld:
    world = make_world(params)
    opening(world)
    world.para()
    jar_disappears(world)
    world.para()
    repeat_and_reason(world)
    world.para()
    use_tool(world)
    close_story(world)
    return world


def generation_prompts(world: SesameWorld) -> list[str]:
    place = PLACES[world.params.place]
    clue = CLUES[world.params.clue]
    tool = TOOLS[world.params.tool]
    return [
        "Write a child-facing rhyming story with sesame, a repeated sesame line, and a gentle solve.",
        f"The first turn should show the clue pointing toward {place.label} instead of random guessing.",
        f"End with a concrete image of success: {world.facts['ending_image']} The rhyme should repeat three times and cause a calm turn in the mystery.",
        f"Use the helper action {tool.label} only when matching the obstruction that caused the problem.",
        f"Keep curiosity central and include the exact line: {clue.line}",
    ]


def story_grounded_qa(world: SesameWorld) -> list[QAItem]:
    place = PLACES[world.params.place]
    clue = CLUES[world.params.clue]
    tool = TOOLS[world.params.tool]

    attempts = int(world.facts.get("repetitions", 0))
    return [
        QAItem(
            question="Why did Lila and Piper repeat the sesame line instead of searching everywhere?",
            answer=(
                f"They repeated the line {attempts} times to keep the clue itself consistent. "
                f"The first two tries felt vague, but repetition let them compare each result and notice the real pattern that pointed to one place."
            ),
        ),
        QAItem(
            question="Where did the sesame jar end up, and why?",
            answer=(
                f"The jar ended up {place.label}, hidden {place.hide_spot}. "
                f"That place fits the clue context because the rhyme line pointed there and the obstruction there was {place.obstacle.lower()}"
            ),
        ),
        QAItem(
            question="What made the final turn possible?",
            answer=(
                f"The decisive turn came when they matched the repeated clue with the right helper tool, {tool.label}. "
                f"That choice solved the right physical obstruction, so the jar could be released safely and the sesame seeds became visible again."
            ),
        ),
        QAItem(
            question="How is the ending different from the beginning?",
            answer=(
                f"At the start, the sesame jar was missing and hidden, and the room felt tense. "
                f"By the ending, {world.facts['ending_image']} which shows the problem was solved in the physical world, not just in words."
            ),
        ),
        QAItem(
            question="What did curiosity look like in this story?",
            answer=(
                f"Curiosity was shown through careful repetition, not wild guessing: the children stayed on the rhyme and kept observing concrete clues. "
                f"That patience gave them the location, the method, and proof of what had really happened."
            ),
        ),
    ]


def world_knowledge_qa(world: SesameWorld) -> list[QAItem]:
    place = PLACES[world.params.place]
    tool = TOOLS[world.params.tool]
    return [
        QAItem(
            question="Why can repetition help in a small search problem like this?",
            answer=(
                f"Repetition makes a noisy scene quieter by filtering accidental signals. "
                f"When the same line is repeated, the part that stays stable becomes the reliable clue, which is exactly what the children used."
            ),
        ),
        QAItem(
            question="Why should a tool be matched to the obstruction rather than forcing the object open?",
            answer=(
                f"For each obstruction, a matching action preserves the object and gives safer control. "
                f"In this story, the match was direct: {tool.label} was chosen because {tool.reason.lower()}."
            ),
        ),
        QAItem(
            question="What is a lesson about clues and evidence from this scenario?",
            answer=(
                f"A clue is most useful when someone can check it against the world directly. "
                f"The physical evidence at {place.label} and the method fit together, so the children moved from a hypothesis to verified recovery."
            ),
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    ok, reason = valid_params(params)
    if not ok:
        raise StoryError(reason)
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_grounded_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
valid(P,C,T) :-
    place(P), clue(C), tool(T),
    clue_points(C, P),
    tool_solves(T, K), place_lock(P, K).

ok :- chosen(P, C, T), valid(P, C, T).

#show valid/3.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from asp import fact

    rows: list[str] = []
    for key, place in PLACES.items():
        rows.append(fact("place", key))
        rows.append(fact("place_lock", key, place.lock))
    for key, clue in CLUES.items():
        rows.append(fact("clue", key))
        rows.append(fact("clue_points", key, clue.place))
    for key, tool in TOOLS.items():
        rows.append(fact("tool", key))
        rows.append(fact("tool_solves", key, tool.solves))
    if params is not None:
        rows.append(fact("chosen", params.place, params.clue, params.tool))
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None, show: str = "") -> str:
    return asp_facts(params) + "\n" + ASP_RULES + "\n" + show


def asp_valid_combos() -> set[tuple[str, str, str]]:
    from asp import atoms, solve

    combos = set()
    for model in solve(asp_program(show=""), models=0):
        for combo in atoms(model, "valid"):
            place, clue, tool = combo
            combos.add((str(place), str(clue), str(tool)))
    return combos


def asp_accepts(params: StoryParams) -> bool:
    from asp import atoms, one_model

    return bool(atoms(one_model(asp_program(params, "#show ok/0.")), "ok"))


def verify() -> str:
    python_combos = {(p.place, p.clue, p.tool) for p in all_params()}
    logic_combos = asp_valid_combos()
    if python_combos != logic_combos:
        only_python = sorted(python_combos - logic_combos)
        only_logic = sorted(logic_combos - python_combos)
        raise StoryError(f"ASP/Python mismatch. only_python={only_python} only_asp={only_logic}")

    for params in all_params():
        if not asp_accepts(params):
            raise StoryError(f"ASP rejected valid params: {params}")

        sample = generate(params)
        story = sample.story.lower()
        world = sample.world
        if "sesame" not in story:
            raise StoryError(f"story missing required word for params={params}")
        if sample.world is None:
            raise StoryError(f"story missing world model for params={params}")
        if world.facts.get("repetitions", 0) != 3:
            raise StoryError(f"repetition count not recorded correctly for params={params}")
        if story.count("\n\n") < 3:
            raise StoryError(f"story lacks clear beginning/turn/ending for params={params}")
        if len(sample.story_qa) < 4:
            raise StoryError(f"story-grounded QA too short for params={params}")
        if len(sample.world_qa) < 3:
            raise StoryError(f"world QA too short for params={params}")
        if sample.world.get("jar").meters.get("open", 0.0) < 1.0:
            raise StoryError(f"jar was never opened for params={params}")
        if sample.world.get("jar").meters.get("present", 0.0) < 1.0:
            raise StoryError(f"jar was never restored for params={params}")
        if not world.facts.get("resolved"):
            raise StoryError(f"story did not mark resolved state for params={params}")

    return f"OK: ASP matches Python for {len(python_combos)} valid sesame stories, and each one resolves to opened sesame seeds with 3-line repetition and full QA."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sesame + repetition + curiosity rhyming storyworld.")
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--clue", choices=sorted(CLUES))
    parser.add_argument("--tool", choices=sorted(TOOLS))
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random | None = None) -> StoryParams:
    rng = rng or random.Random(args.seed)
    explicit = any(getattr(args, key) is not None for key in ("place", "clue", "tool"))

    combos = [
        p
        for p in all_params()
        if (args.place is None or args.place == p.place)
        and (args.clue is None or args.clue == p.clue)
        and (args.tool is None or args.tool == p.tool)
    ]
    if not combos:
        raise StoryError(explain_invalid(args.place, args.clue, args.tool))

    chosen = combos[rng.randrange(len(combos))]
    return StoryParams(chosen.place, chosen.clue, chosen.tool, seed=args.seed)


def _trace_lines(world: SesameWorld) -> list[str]:
    jar = world.get("jar")
    seeds = world.get("seeds")
    lila = world.get("lila")
    piper = world.get("piper")
    lines = ["Trace:"]
    for event in world.history:
        lines.append(f"- {event.id}: {event.text}")
    lines.append("State:")
    lines.append(f"  jar_present={jar.meters['present']:.1f} jar_open={jar.meters['open']:.1f} jar_hidden={jar.meters['hidden']:.1f}")
    lines.append(f"  lila_curiosity={lila.memes['curiosity']:.1f} piper_curiosity={piper.memes['curiosity']:.1f}")
    lines.append(f"  seeds_ready={seeds.meters.get('ready_for_bake', 0.0):.1f} repetitions={world.facts.get('repetitions', 0)}")
    return lines


def _format_qa(sample: StorySample) -> str:
    rows = ["Prompts:"]
    for prompt in sample.prompts:
        rows.append(f"- {prompt}")
    rows.append("")
    rows.append("Story-grounded QA:")
    for item in sample.story_qa:
        rows.append(f"Q: {item.question}")
        rows.append(f"A: {item.answer}")
    rows.append("")
    rows.append("World-knowledge QA:")
    for item in sample.world_qa:
        rows.append(f"Q: {item.question}")
        rows.append(f"A: {item.answer}")
    return "\n".join(rows)


def emit(sample: StorySample, args: argparse.Namespace, header: str | None = None) -> None:
    if args.json:
        payload = sample.to_dict()
        if header:
            payload = {"header": header, **payload}
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    if header:
        print(header)
    print(sample.story)

    if args.trace:
        print()
        print("\n".join(_trace_lines(sample.world)))

    if args.qa:
        print()
        print(_format_qa(sample))


def _sample_n(args: argparse.Namespace) -> list[StorySample]:
    combos = all_params()
    if args.place is not None or args.clue is not None or args.tool is not None:
        filtered = [p for p in combos if (args.place is None or args.place == p.place)
                    and (args.clue is None or args.clue == p.clue)
                    and (args.tool is None or args.tool == p.tool)]
    else:
        filtered = combos
    if not filtered:
        raise StoryError(explain_invalid(args.place, args.clue, args.tool))
    if args.n <= 0:
        raise StoryError("--n must be a positive integer")

    rng = random.Random(args.seed)
    samples: list[StorySample] = []
    for index in range(args.n):
        base = filtered[index % len(filtered)]
        samples.append(
            generate(StoryParams(place=base.place, clue=base.clue, tool=base.tool, seed=args.seed + index if args.seed is not None else None))
        )
    return samples


def _sample_all(args: argparse.Namespace) -> list[StorySample]:
    samples: list[StorySample] = []
    for index, base in enumerate(all_params()):
        samples.append(
            generate(StoryParams(place=base.place, clue=base.clue, tool=base.tool, seed=(args.seed or 13) + index))
        )
    return samples


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        if args.show_asp:
            print(asp_program(show="#show valid/3."))
            return 0
        if args.verify:
            print(verify())
            return 0
        if args.asp:
            for combo in sorted(asp_valid_combos()):
                print("\t".join(combo))
            return 0

        samples = _sample_all(args) if args.all else _sample_n(args)

        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
            return 0

        for index, sample in enumerate(samples):
            header = f"### variant {index + 1}" if len(samples) > 1 else None
            emit(sample, args, header=header)
            if index + 1 < len(samples):
                print("\n---\n")
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
