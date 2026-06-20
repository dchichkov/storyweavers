#!/usr/bin/env python3
"""Mythic riverbank mystery about a cozy tree, suspense, and teamwork."""

from __future__ import annotations

import argparse
import copy
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample

THRESHOLD = 1.0


@dataclass(frozen=True)
class RiverTree:
    key: str
    label: str
    shelter: str
    omen: str
    supports: tuple[str, ...]


@dataclass(frozen=True)
class Relic:
    key: str
    label: str
    material: str
    purpose: str
    valid_places: tuple[str, ...]
    clue_effect: str
    closing_image: str


@dataclass(frozen=True)
class Mystery:
    key: str
    place: str
    place_label: str
    loss_line: str
    clue: str
    cause: str
    suspense_line: str
    recovery_line: str


@dataclass(frozen=True)
class Plan:
    key: str
    label: str
    clears: tuple[str, ...]
    job_a: str
    job_b: str
    proof_line: str


@dataclass
class StoryParams:
    tree: str
    relic: str
    mystery: str
    plan: str
    hero: str
    hero_gender: str
    partner: str
    partner_gender: str
    seed: int | None = None


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Event:
    id: str
    text: str
    subject: str
    target: str | None = None


@dataclass
class RiverWorld:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def record(self, event_id: str, text: str, subject: str, target: str | None = None) -> None:
        self.history.append(Event(event_id, text, subject, target))

    def copy(self) -> "RiverWorld":
        return copy.deepcopy(self)

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for ent in self.entities.values():
            meters = {k: v for k, v in ent.meters.items() if v}
            memes = {k: v for k, v in ent.memes.items() if v}
            extras = []
            if ent.role:
                extras.append(f"role={ent.role}")
            if meters:
                extras.append(f"meters={dict(meters)}")
            if memes:
                extras.append(f"memes={dict(memes)}")
            if ent.attrs:
                extras.append(f"attrs={dict(ent.attrs)}")
            lines.append(f"  {ent.id:8} ({ent.type:12}) {ent.label} {' '.join(extras)}")
        lines.append("  history:")
        for event in self.history:
            lines.append(f"    - {event.id}: {event.text}")
        return "\n".join(lines)


TREES: dict[str, RiverTree] = {
    "willow": RiverTree(
        "willow",
        "the cozy willow tree",
        "its hanging branches made a warm green room above the slow water",
        "The willow leaves whispered so softly that the children could hear the river thinking.",
        ("reeds", "roots"),
    ),
    "alder": RiverTree(
        "alder",
        "the cozy alder tree",
        "its roots braided a little bench where children could tuck their feet",
        "The alder roots shed bright drops into the dusk as if counting how little light remained.",
        ("roots", "stone"),
    ),
    "sycamore": RiverTree(
        "sycamore",
        "the cozy sycamore tree",
        "its pale limbs curved into a snug lookout over the water",
        "The sycamore bark shone like moonbread while the river held its breath.",
        ("reeds", "stone"),
    ),
}

RELICS: dict[str, Relic] = {
    "moon_bell": Relic(
        "moon_bell",
        "the moon-bell",
        "bronze",
        "so the ferry spirits remembered the safe path home",
        ("reeds", "roots"),
        "a dim silver glint",
        "the moon-bell rang once, and a clear path shone between the dark ripples",
    ),
    "ferry_shell": Relic(
        "ferry_shell",
        "the ferry-shell charm",
        "pearl",
        "so the night current would carry boats toward the gentle bank instead of the deep bend",
        ("reeds", "stone"),
        "a pale pearly flash",
        "the ferry-shell charm glowed softly, and the water leaned back toward the gentle bank",
    ),
    "reed_ring": Relic(
        "reed_ring",
        "the reed-lantern ring",
        "woven rush and tin",
        "so the dusk lantern on the bank would answer the river spirits before fog could hide the crossing",
        ("roots", "stone"),
        "a trapped lantern blink",
        "the reed-lantern ring caught the last gold of evening, and the first thin fog folded itself away",
    ),
}

MYSTERIES: dict[str, Mystery] = {
    "reed_snag": Mystery(
        "reed_snag",
        "reeds",
        "the whispering reeds",
        "When the children reached for the relic, only its cord was left, trailing toward the whispering reeds.",
        "a narrow lane of bent reeds and a small flash trembling between them",
        "the quick current had combed it into the reeds and pinned it there",
        "If the relic stayed hidden there, the evening ferry would meet only guesses and dark water.",
        "At the heart of the reeds, the lost relic waited where the current had woven a secret pocket.",
    ),
    "root_cradle": Mystery(
        "root_cradle",
        "roots",
        "the root cradle",
        "When the children reached for the relic, it was gone, and damp mud showed a round mark below the tree roots.",
        "a dark hollow under the roots, marked by fresh mud and the relic's own faint shimmer",
        "a river gust had rolled it into a cradle beneath the roots",
        "If the relic stayed hidden there, the bank lantern would speak into fog and no spirit would know which answer to trust.",
        "Inside the root cradle, the lost relic rested where the bank had cupped it like a secret hand.",
    ),
    "otter_stone": Mystery(
        "otter_stone",
        "stone",
        "the otter-stone",
        "When the children reached for the relic, only a wet circle remained, and tiny paw prints led toward the flat otter-stone.",
        "a ring of wet paw prints and a patient gleam warming on the flat stone near the shallows",
        "a playful otter had nudged it onto the warm stone and forgotten it when the singing stopped",
        "If the relic stayed hidden there, the deep bend would borrow the river's voice before the last boat came home.",
        "On the otter-stone, the lost relic lay bright and still above the shallows.",
    ),
}

PLANS: dict[str, Plan] = {
    "pole_reeds": Plan(
        "pole_reeds",
        "steady the bank rope and part the reeds",
        ("reeds",),
        "brace the old bank rope so no one slipped",
        "part the reeds with the heron pole and follow the glint",
        "Because one child held steady while the other searched, the reeds opened without swallowing either of them.",
    ),
    "lantern_roots": Plan(
        "lantern_roots",
        "hold a jar lantern low and search the root cradle",
        ("roots",),
        "hold the jar lantern close to the mud without letting it shake",
        "reach into the root cradle and feel for the relic beneath the cool water",
        "Because one child kept the light still while the other searched, the roots gave up their hidden shape instead of hiding it deeper.",
    ),
    "rope_stone": Plan(
        "rope_stone",
        "tighten the ferry rope and step to the otter-stone",
        ("stone",),
        "pull the ferry rope tight across the shallows",
        "step to the flat stone and lift the relic before the current turned it away again",
        "Because one child measured the water while the other moved, the shallows became a path instead of a danger.",
    ),
}

GIRL_NAMES = ["Nara", "Lina", "Mira", "Tala"]
BOY_NAMES = ["Ivo", "Oren", "Sami", "Tarin"]
TRAITS = ["patient", "keen-eyed", "steady", "brave"]

KNOWLEDGE = {
    "relic": (
        "Why did the riverbank children hang a relic in the tree at dusk?",
        "In this little myth, the relic is a signal for river spirits. It tells them which path is gentle enough for boats and feet.",
    ),
    "reeds": (
        "Why can reeds hide small things?",
        "Reeds bend together and make narrow pockets. A light object can slip between them and stay there until someone parts the stalks.",
    ),
    "roots": (
        "Why can tree roots keep a secret?",
        "Roots can make bowls and hollows where water leaves small treasures. Mud also holds marks that help careful searchers read what happened.",
    ),
    "stone": (
        "Why is a flat river stone useful in a mystery?",
        "A flat stone catches whatever the current nudges onto it. It also keeps clear tracks like wet paw prints or a shining object in one place.",
    ),
    "teamwork": (
        "Why did teamwork matter at the riverbank?",
        "Near water, one child can watch the ground, rope, or light while the other reaches or steps. That keeps the search careful instead of reckless.",
    ),
}


def sentence_start(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


def failure_consequence(relic: Relic) -> str:
    return {
        "moon_bell": "the ferry spirits would forget the gentle path and drift toward darker water",
        "ferry_shell": "the night current would tug boats toward the deep bend instead of the gentle bank",
        "reed_ring": "the first fog would cover the crossing before the river spirits heard the bank's answer",
    }[relic.key]


def valid_combo(tree: RiverTree, relic: Relic, mystery: Mystery, plan: Plan) -> bool:
    return (
        mystery.place in tree.supports
        and mystery.place in relic.valid_places
        and mystery.place in plan.clears
    )


def explain_rejection(tree: RiverTree, relic: Relic, mystery: Mystery, plan: Plan) -> str:
    if mystery.place not in tree.supports:
        return f"(No story: {tree.label} does not overlook {mystery.place_label}.)"
    if mystery.place not in relic.valid_places:
        return f"(No story: {relic.label} would not plausibly end up at {mystery.place_label}.)"
    return f"(No story: the plan '{plan.label}' does not actually clear {mystery.place_label}.)"


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for tree_id, tree in TREES.items():
        for relic_id, relic in RELICS.items():
            for mystery_id, mystery in MYSTERIES.items():
                for plan_id, plan in PLANS.items():
                    if valid_combo(tree, relic, mystery, plan):
                        combos.append((tree_id, relic_id, mystery_id, plan_id))
    return sorted(combos)


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [name for name in pool if name != avoid]
    return rng.choice(options)


def make_world(params: StoryParams) -> RiverWorld:
    tree = TREES[params.tree]
    relic = RELICS[params.relic]
    mystery = MYSTERIES[params.mystery]
    plan = PLANS[params.plan]

    world = RiverWorld(params)
    hero = world.add(
        Entity(
            "hero",
            "character",
            params.hero_gender,
            params.hero,
            role="watcher",
            traits=[TRAITS[(params.seed or 0) % len(TRAITS)]],
        )
    )
    partner = world.add(
        Entity(
            "partner",
            "character",
            params.partner_gender,
            params.partner,
            role="helper",
            traits=[TRAITS[((params.seed or 0) + 1) % len(TRAITS)]],
        )
    )
    pair = world.add(Entity("pair", "group", "children", f"{params.hero} and {params.partner}", role="team"))
    tree_ent = world.add(Entity("tree", "place", "tree", tree.label))
    river = world.add(Entity("river", "place", "riverbank", "the riverbank"))
    relic_ent = world.add(Entity("relic", "object", "relic", relic.label))
    site = world.add(Entity("site", "place", mystery.place, mystery.place_label))

    tree_ent.meters["shelter"] = 1.0
    tree_ent.meters["height"] = 1.0
    tree_ent.memes["welcome"] = 1.0
    river.meters["twilight"] = 1.0
    river.meters["safe_path"] = 1.0
    river.memes["mystery"] = 0.0
    river.memes["suspense"] = 0.0
    relic_ent.meters["hung"] = 1.0
    relic_ent.meters["lost"] = 0.0
    relic_ent.attrs["location"] = "tree"
    pair.memes["trust"] = 2.0
    pair.memes["teamwork"] = 0.0
    hero.memes["duty"] = 1.0
    partner.memes["duty"] = 1.0
    site.attrs["place"] = mystery.place

    world.facts.update(
        tree=tree,
        relic=relic,
        mystery=mystery,
        plan=plan,
        hero=hero,
        partner=partner,
        pair=pair,
        resolved=False,
        source_tale=(
            "Two riverbank children keep a dusk relic in a cozy tree so the ferry spirits "
            "remember the safe crossing. When it vanishes at sunset, they must follow the "
            "bank's clues together before darkness confuses the river."
        ),
    )
    return world


def recalculate(world: RiverWorld) -> None:
    pair = world.get("pair")
    river = world.get("river")
    relic = world.get("relic")

    river.meters["safe_path"] = 1.0 if relic.meters["hung"] >= THRESHOLD else 0.0
    river.memes["mystery"] = 1.0 if relic.meters["lost"] >= THRESHOLD else 0.0
    river.memes["suspense"] = 1.0 if relic.meters["lost"] >= THRESHOLD and river.meters["twilight"] >= THRESHOLD else 0.0
    pair.memes["relief"] = 1.0 if relic.meters["hung"] >= THRESHOLD and pair.memes["teamwork"] >= THRESHOLD else 0.0
    world.facts["resolved"] = bool(relic.meters["hung"] >= THRESHOLD and pair.memes["teamwork"] >= THRESHOLD)


def opening(world: RiverWorld) -> None:
    tree = TREES[world.params.tree]
    relic = RELICS[world.params.relic]
    hero = world.get("hero")
    partner = world.get("partner")
    world.record(
        "opening",
        f"Under a cozy tree on the riverbank, {tree.shelter}. Each dusk {hero.label} and {partner.label} climbed there to hang {relic.label} so the ferry spirits would remember the gentle crossing.",
        "tree",
        "relic",
    )


def loss_and_omen(world: RiverWorld) -> None:
    mystery = MYSTERIES[world.params.mystery]
    tree = TREES[world.params.tree]
    pair = world.get("pair")
    river = world.get("river")
    relic = world.get("relic")
    hero = world.get("hero")

    relic.meters["hung"] = 0.0
    relic.meters["lost"] = 1.0
    relic.attrs["location"] = mystery.place
    pair.memes["worry"] += 1.0
    hero.memes["alarm"] += 1.0
    river.meters["current"] += 1.0
    recalculate(world)

    world.record("loss", mystery.loss_line, "hero", "relic")
    world.record("omen", f"{tree.omen} {mystery.suspense_line}", "river", mystery.place)


def forecast_without_help(world: RiverWorld) -> str:
    imagined = world.copy()
    imagined.get("river").meters["twilight"] += 1.0
    recalculate(imagined)
    relic = RELICS[imagined.params.relic]
    if imagined.get("river").memes["suspense"] >= THRESHOLD:
        return (
            f"If {relic.label} stayed lost much longer, the dusk path would go blind, "
            f"and {failure_consequence(relic)}."
        )
    return f"If {relic.label} stayed lost, the children would lose more than a keepsake."


def inspect_clue(world: RiverWorld) -> None:
    mystery = MYSTERIES[world.params.mystery]
    relic = RELICS[world.params.relic]
    site = world.get("site")
    pair = world.get("pair")
    partner = world.get("partner")

    site.meters["marked"] = 1.0
    site.meters["glimmer"] = 1.0
    pair.memes["curiosity"] += 1.0
    partner.memes["focus"] += 1.0
    world.record(
        "clue",
        f"Then {partner.label} knelt by the bank and noticed {mystery.clue}. It was {relic.clue_effect}, just enough to tell the children that the river had hidden a true clue instead of playing a trick.",
        "partner",
        "site",
    )


def choose_plan(world: RiverWorld) -> None:
    plan = PLANS[world.params.plan]
    hero = world.get("hero")
    partner = world.get("partner")
    pair = world.get("pair")

    pair.memes["teamwork"] += 1.0
    hero.memes["courage"] += 1.0
    partner.memes["courage"] += 1.0
    recalculate(world)
    world.record(
        "plan",
        f'"We will not search like frightened sparrows," {hero.label} said. {hero.label} would {plan.job_a}, and {partner.label} would {plan.job_b}.',
        "pair",
        "site",
    )


def recover_relic(world: RiverWorld) -> None:
    mystery = MYSTERIES[world.params.mystery]
    plan = PLANS[world.params.plan]
    pair = world.get("pair")
    relic = world.get("relic")
    site = world.get("site")

    if site.meters["marked"] < THRESHOLD or pair.memes["teamwork"] < THRESHOLD:
        raise StoryError("the children tried to solve the mystery before the clue and teamwork were in place")

    relic.meters["lost"] = 0.0
    relic.meters["found"] = 1.0
    relic.attrs["location"] = mystery.place
    site.meters["searched"] = 1.0
    pair.memes["trust"] += 0.5
    recalculate(world)
    world.record(
        "recover",
        f"{plan.proof_line} {mystery.recovery_line} The children understood that {mystery.cause}.",
        "pair",
        "relic",
    )


def restore_balance(world: RiverWorld) -> None:
    relic_cfg = RELICS[world.params.relic]
    relic = world.get("relic")
    river = world.get("river")
    tree = world.get("tree")
    pair = world.get("pair")
    hero = world.get("hero")
    partner = world.get("partner")

    relic.meters["hung"] = 1.0
    relic.attrs["location"] = "tree"
    river.meters["current"] = max(0.0, river.meters["current"] - 1.0)
    river.meters["calm"] = 1.0
    tree.memes["peace"] += 1.0
    pair.memes["joy"] += 1.0
    recalculate(world)
    world.facts["closing_image"] = relic_cfg.closing_image
    world.record(
        "restore",
        f"{hero.label} and {partner.label} hung {relic_cfg.label} back in the tree. {sentence_start(relic_cfg.closing_image)}, and the riverbank grew gentle enough for even the smallest boat to trust.",
        "pair",
        "tree",
    )


def render_story(world: RiverWorld, forecast: str) -> str:
    parts = [
        " ".join([world.history[0].text]),
        " ".join([world.history[1].text, world.history[2].text, forecast]),
        " ".join([world.history[3].text, world.history[4].text, world.history[5].text]),
        world.history[6].text,
    ]
    return "\n\n".join(parts)


def generation_prompts(world: RiverWorld) -> list[str]:
    tree = TREES[world.params.tree]
    mystery = MYSTERIES[world.params.mystery]
    return [
        'Write a child-facing myth set on a riverbank that includes the words "cozy tree".',
        f"Tell a suspenseful teamwork mystery in which two children follow a clue toward {mystery.place_label}.",
        f"Keep the tone warm and mythical, beginning beneath {tree.label} and ending with a visible sign that the river has changed.",
    ]


def story_qa_items(world: RiverWorld) -> list[QAItem]:
    hero = world.get("hero")
    partner = world.get("partner")
    relic = RELICS[world.params.relic]
    mystery = MYSTERIES[world.params.mystery]
    plan = PLANS[world.params.plan]
    return [
        QAItem(
            "Why were the children under the cozy tree at dusk?",
            f"{hero.label} and {partner.label} were there to hang {relic.label} in the tree before night deepened. In their riverbank myth, that relic helped the ferry spirits remember the safe crossing.",
        ),
        QAItem(
            "What clue told them where to search?",
            f"The clue was {mystery.clue}. It pointed them toward {mystery.place_label}, so they chased evidence instead of guessing in fear.",
        ),
        QAItem(
            "How did teamwork help solve the mystery?",
            f"They followed the plan to {plan.label}. One child kept the search safe while the other made the careful reach, so the clue could turn into proof.",
        ),
        QAItem(
            "What changed after the relic was returned?",
            f"After the relic was rehung, the river stopped feeling uncertain and dangerous. {world.facts['closing_image'].capitalize()}, which showed that the crossing was gentle again.",
        ),
    ]


def world_knowledge_items(world: RiverWorld) -> list[QAItem]:
    mystery = MYSTERIES[world.params.mystery]
    items = [QAItem(*KNOWLEDGE["relic"]), QAItem(*KNOWLEDGE["teamwork"]), QAItem(*KNOWLEDGE[mystery.place])]
    return items


def generate(params: StoryParams) -> StorySample:
    tree = TREES[params.tree]
    relic = RELICS[params.relic]
    mystery = MYSTERIES[params.mystery]
    plan = PLANS[params.plan]
    if not valid_combo(tree, relic, mystery, plan):
        raise StoryError(explain_rejection(tree, relic, mystery, plan))

    world = make_world(params)
    opening(world)
    loss_and_omen(world)
    forecast = forecast_without_help(world)
    inspect_clue(world)
    choose_plan(world)
    recover_relic(world)
    restore_balance(world)
    story = render_story(world, forecast)
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa_items(world),
        world_qa=world_knowledge_items(world),
        world=world,
    )


ASP_RULES = r"""
host(T,Place) :- supports(T,Place).
plausible(R,Place) :- relic_place(R,Place).
plan_clears(P,Place) :- clears(P,Place).
valid(T,R,M,P) :-
    tree(T), relic(R), mystery(M), plan(P),
    mystery_place(M,Place),
    host(T,Place),
    plausible(R,Place),
    plan_clears(P,Place).
"""


def asp_facts() -> str:
    from storyworlds import asp

    lines: list[str] = []
    for tree_id, tree in TREES.items():
        lines.append(asp.fact("tree", tree_id))
        for place in tree.supports:
            lines.append(asp.fact("supports", tree_id, place))
    for relic_id, relic in RELICS.items():
        lines.append(asp.fact("relic", relic_id))
        for place in relic.valid_places:
            lines.append(asp.fact("relic_place", relic_id, place))
    for mystery_id, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mystery_id))
        lines.append(asp.fact("mystery_place", mystery_id, mystery.place))
    for plan_id, plan in PLANS.items():
        lines.append(asp.fact("plan", plan_id))
        for place in plan.clears:
            lines.append(asp.fact("clears", plan_id, place))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> set[tuple[str, str, str, str]]:
    from storyworlds import asp

    model = asp.one_model(asp_program())
    return {tuple(item) for item in asp.atoms(model, "valid")}


def verify() -> str:
    python_combos = set(valid_combos())
    asp_combos = asp_valid_combos()
    if python_combos != asp_combos:
        only_python = sorted(python_combos - asp_combos)
        only_asp = sorted(asp_combos - python_combos)
        raise StoryError(f"ASP/Python mismatch. only_python={only_python} only_asp={only_asp}")

    for index, combo in enumerate(sorted(python_combos)):
        params = StoryParams(
            tree=combo[0],
            relic=combo[1],
            mystery=combo[2],
            plan=combo[3],
            hero="Nara",
            hero_gender="girl",
            partner="Ivo",
            partner_gender="boy",
            seed=index,
        )
        sample = generate(params)
        if "cozy tree" not in sample.story or "riverbank" not in sample.story:
            raise StoryError(f"seed essentials dropped for combo {combo}")
        if sample.story.count("\n\n") < 3:
            raise StoryError(f"story shape is too thin for combo {combo}")
        if len(sample.story_qa) < 4 or len(sample.world_qa) < 3:
            raise StoryError(f"QA set is too thin for combo {combo}")
        if not sample.world or not sample.world.facts.get("resolved"):
            raise StoryError(f"world never resolved for combo {combo}")
        if sentence_start(str(sample.world.facts.get("closing_image", ""))) not in sample.story:
            raise StoryError(f"final image is missing for combo {combo}")
    return f"OK: Python and ASP gates agree and exercised {len(python_combos)} mythic riverbank stories."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate cozy-tree riverbank myth samples.")
    parser.add_argument("--tree", choices=sorted(TREES))
    parser.add_argument("--relic", choices=sorted(RELICS))
    parser.add_argument("--mystery", choices=sorted(MYSTERIES))
    parser.add_argument("--plan", choices=sorted(PLANS))
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def _params_from_combo(combo: tuple[str, str, str, str], seed: int) -> StoryParams:
    rng = random.Random(seed)
    hero_gender = rng.choice(["girl", "boy"])
    partner_gender = "boy" if hero_gender == "girl" else "girl"
    hero = _pick_name(rng, hero_gender)
    partner = _pick_name(rng, partner_gender, avoid=hero)
    return StoryParams(
        tree=combo[0],
        relic=combo[1],
        mystery=combo[2],
        plan=combo[3],
        hero=hero,
        hero_gender=hero_gender,
        partner=partner,
        partner_gender=partner_gender,
        seed=seed,
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        combo
        for combo in valid_combos()
        if (args.tree is None or combo[0] == args.tree)
        and (args.relic is None or combo[1] == args.relic)
        and (args.mystery is None or combo[2] == args.mystery)
        and (args.plan is None or combo[3] == args.plan)
    ]
    if not combos:
        tree = TREES[args.tree] if args.tree else next(iter(TREES.values()))
        relic = RELICS[args.relic] if args.relic else next(iter(RELICS.values()))
        mystery = MYSTERIES[args.mystery] if args.mystery else next(iter(MYSTERIES.values()))
        plan = PLANS[args.plan] if args.plan else next(iter(PLANS.values()))
        raise StoryError(explain_rejection(tree, relic, mystery, plan))
    combo = rng.choice(combos)
    seed = rng.randint(0, 2**31 - 1)
    return _params_from_combo(combo, seed)


def _samples_for_all(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed
    samples: list[StorySample] = []
    for index, combo in enumerate(valid_combos()):
        story_seed = base_seed + index
        params = _params_from_combo(combo, story_seed)
        samples.append(generate(params))
    return samples


def _samples_for_n(args: argparse.Namespace) -> list[StorySample]:
    rng = random.Random(args.seed)
    samples: list[StorySample] = []
    seen: set[str] = set()
    attempts = 0
    target = max(1, args.n)
    while len(samples) < target and attempts < target * 40:
        attempts += 1
        sample = generate(resolve_params(args, rng))
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    if len(samples) < target:
        raise StoryError(f"could not generate {target} distinct samples from the requested constraints")
    return samples


def emit(sample: StorySample, args: argparse.Namespace) -> None:
    if args.json:
        print(sample.to_json())
        return
    print(sample.story)
    if args.trace and sample.world is not None:
        print()
        print(sample.world.trace())
    if args.qa:
        print()
        print("== (1) Generation prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print()
        print("== (2) Story-grounded QA ==")
        for qa in sample.story_qa:
            print(f"Q: {qa.question}")
            print(f"A: {qa.answer}")
        print()
        print("== (3) World-knowledge QA ==")
        for qa in sample.world_qa:
            print(f"Q: {qa.question}")
            print(f"A: {qa.answer}")


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
            combos = sorted(asp_valid_combos())
            print(f"{len(combos)} valid (tree, relic, mystery, plan) combos:\n")
            for combo in combos:
                print("  " + " ".join(f"{part:14}" for part in combo))
            return 0

        samples = _samples_for_all(args) if args.all else _samples_for_n(args)
        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
            return 0

        for index, sample in enumerate(samples):
            if index:
                print("\n" + "=" * 70 + "\n")
            emit(sample, args)
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
