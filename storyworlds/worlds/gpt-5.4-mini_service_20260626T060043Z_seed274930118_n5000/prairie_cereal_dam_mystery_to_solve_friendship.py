#!/usr/bin/env python3
"""
A tiny story world: prairie, cereal, dam, mystery to solve, and friendship,
told in a nursery-rhyme style.

A child-friendly premise:
- On a wide prairie, friends find a puzzling cereal trail near a little dam.
- The trail turns into a mystery to solve: who tipped the cereal, and why is the dam leaking?
- The friends follow clues, work together, and fix the problem.
- Friendship grows because they share the solving.

The simulated world uses:
- physical meters: spilled cereal, leak, wetness, repairedness, clue strength
- emotional memes: curiosity, worry, teamwork, relief, friendship

The story generation is not a frozen paragraph. It advances a small state model:
setup -> clue hunt -> discovery -> repair -> celebration.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Place:
    id: str
    name: str
    detail: str


@dataclass(frozen=True)
class CharacterSpec:
    id: str
    name: str
    kind: str
    role: str
    rhyme: str


@dataclass(frozen=True)
class MysterySpec:
    id: str
    clue_word: str
    spill_word: str
    fix_word: str
    ending_image: str


@dataclass(frozen=True)
class ToolSpec:
    id: str
    name: str
    purpose: str


PLACES = {
    "prairie": Place(
        id="prairie",
        name="the prairie",
        detail="The grass was gold and the sky was wide and blue.",
    )
}

CHARACTERS = {
    "bunny": CharacterSpec(id="bunny", name="Nell the bunny", kind="bunny", role="finder", rhyme="hopping"),
    "fox": CharacterSpec(id="fox", name="Milo the fox", kind="fox", role="helper", rhyme="trotting"),
    "mouse": CharacterSpec(id="mouse", name="Dot the mouse", kind="mouse", role="helper", rhyme="scurrying"),
}

MYSTERIES = {
    "cereal_dam": MysterySpec(
        id="cereal_dam",
        clue_word="cereal",
        spill_word="spilled cereal",
        fix_word="patch",
        ending_image="the dam stood quiet under the moon, with cereal tucked away and friends side by side",
    )
}

TOOLS = {
    "bucket": ToolSpec(id="bucket", name="a little bucket", purpose="scoop up cereal"),
    "patch_clay": ToolSpec(id="patch_clay", name="sticky clay", purpose="seal the dam"),
    "brush": ToolSpec(id="brush", name="a soft brush", purpose="sweep crumbs"),
}


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    name: str
    kind: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    held: set[str] = field(default_factory=set)

    def get_meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def add_meter(self, key: str, value: float) -> None:
        self.meters[key] = self.get_meter(key) + value

    def add_meme(self, key: str, value: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + value


@dataclass
class World:
    place: Place
    mystery: MysterySpec
    characters: dict[str, Entity] = field(default_factory=dict)
    tools: dict[str, Entity] = field(default_factory=dict)
    history: list[str] = field(default_factory=list)
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

    def say(self, line: str) -> None:
        if line:
            self.history.append(line)

    def para(self) -> None:
        if self.history and self.history[-1] != "":
            self.history.append("")

    def add_character(self, spec: CharacterSpec) -> Entity:
        ent = Entity(id=spec.id, name=spec.name, kind="character")
        self.characters[spec.id] = ent
        return ent

    def add_tool(self, spec: ToolSpec) -> Entity:
        ent = Entity(id=spec.id, name=spec.name, kind="tool")
        self.tools[spec.id] = ent
        return ent

    def render(self) -> str:
        out = []
        paragraph = []
        for line in self.history:
            if line == "":
                if paragraph:
                    out.append(" ".join(paragraph))
                    paragraph = []
            else:
                paragraph.append(line)
        if paragraph:
            out.append(" ".join(paragraph))
        return "\n\n".join(out)


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str = "prairie"
    mystery: str = "cereal_dam"
    seed: Optional[int] = None
    lead: str = "bunny"
    helper1: str = "fox"
    helper2: str = "mouse"


PLACE_REGISTRY = list(PLACES.keys())
MYSTERY_REGISTRY = list(MYSTERIES.keys())
CHARACTER_REGISTRY = list(CHARACTERS.keys())


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------

def rhyme_opening(world: World, lead: Entity) -> None:
    world.say(f"On the prairie bright and wide, {lead.name} went out to glide.")
    world.say(f"The wind went hush, the grass said swish, and the day began like a nursery wish.")


def introduce_mystery(world: World, lead: Entity) -> None:
    mystery = world.mystery
    world.say(
        f"By the little dam, {lead.name} found {mystery.spill_word}, all crunchy on the ground."
    )
    world.say(
        f"'Oh dear, oh no,' said {lead.name}, 'this sticky trail is odd to see. "
        f"I wonder who did this, and why the dam cannot be.'"
    )
    lead.add_meme("curiosity", 2.0)
    lead.add_meter("clue_strength", 1.0)
    world.facts["mystery_found"] = True


def search_clues(world: World, lead: Entity, helper1: Entity, helper2: Entity) -> None:
    world.say(
        f"{helper1.name} came trotting near, and {helper2.name} came scurrying near."
    )
    world.say(
        f"Together they looked with careful eyes, because a mystery grows clearer with friends standing near."
    )
    lead.add_meme("friendship", 1.0)
    helper1.add_meme("friendship", 1.0)
    helper2.add_meme("friendship", 1.0)
    lead.add_meme("teamwork", 1.0)
    helper1.add_meme("teamwork", 1.0)
    helper2.add_meme("teamwork", 1.0)
    world.facts["team_formed"] = True


def discover_cause(world: World, lead: Entity, helper1: Entity, helper2: Entity) -> None:
    world.say(
        f"Under a bent reed they found a torn sack of cereal, and little hoofprints in the dust."
    )
    world.say(
        f"'The wind did not tip this,' said {helper1.name}. 'Someone carried it, then dropped it in haste.'"
    )
    lead.add_meme("worry", 1.0)
    world.facts["cause"] = "torn_sack"


def repair_dam(world: World, lead: Entity, helper1: Entity, helper2: Entity) -> None:
    world.add_tool(TOOLS["bucket"])
    world.add_tool(TOOLS["patch_clay"])
    world.add_tool(TOOLS["brush"])

    world.say(
        f"{lead.name} fetched {TOOLS['bucket'].name}, {helper1.name} brought {TOOLS['patch_clay'].name}, "
        f"and {helper2.name} used {TOOLS['brush'].name} to sweep each crumb away."
    )
    lead.add_meter("spilled_cereal", 2.0)
    world.facts["spilled_cereal_seen"] = True

    # Cause and effect: once the cereal is cleared, the dam can be patched.
    if lead.get_meter("spilled_cereal") >= 1.0:
        world.say(
            f"Then they pressed the {world.mystery.fix_word} into the small crack, and the drip went drip no more."
        )
        world.facts["dam_repaired"] = True
        lead.add_meter("dam_repaired", 1.0)
        helper1.add_meter("dam_repaired", 1.0)
        helper2.add_meter("dam_repaired", 1.0)
        lead.add_meme("relief", 2.0)
        helper1.add_meme("relief", 2.0)
        helper2.add_meme("relief", 2.0)


def end_on_friendship(world: World, lead: Entity, helper1: Entity, helper2: Entity) -> None:
    world.say(
        f"{lead.name} smiled big as buttons, because the answer was found and the dam was sound."
    )
    world.say(
        f"{helper1.name} and {helper2.name} laughed beside {lead.name}, and their friendship felt strong and round."
    )
    world.say(world.mystery.ending_image + ".")


def build_world(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.mystery not in MYSTERIES:
        raise StoryError(f"Unknown mystery: {params.mystery}")
    for key in [params.lead, params.helper1, params.helper2]:
        if key not in CHARACTERS:
            raise StoryError(f"Unknown character choice: {key}")
    if len({params.lead, params.helper1, params.helper2}) < 3:
        raise StoryError("Lead and helpers must be three different characters.")

    world = World(place=PLACES[params.place], mystery=MYSTERIES[params.mystery])
    lead = world.add_character(CHARACTERS[params.lead])
    helper1 = world.add_character(CHARACTERS[params.helper1])
    helper2 = world.add_character(CHARACTERS[params.helper2])

    rhyme_opening(world, lead)
    world.para()
    introduce_mystery(world, lead)
    world.para()
    search_clues(world, lead, helper1, helper2)
    discover_cause(world, lead, helper1, helper2)
    world.para()
    repair_dam(world, lead, helper1, helper2)
    end_on_friendship(world, lead, helper1, helper2)

    world.facts.update(
        place=world.place,
        mystery=world.mystery,
        lead=lead,
        helper1=helper1,
        helper2=helper2,
        dam_repaired=bool(world.facts.get("dam_repaired")),
    )
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A mystery exists when cereal is found near the dam.
mystery_found(P) :- place(P), spill(cereal, P), near_dam(P).

% Friendship grows when the friends solve the mystery together.
friendship_grows(L, H1, H2) :- character(L), character(H1), character(H2),
                               L != H1, L != H2, H1 != H2, mystery_found(P),
                               together(L, H1, H2, P), repaired(P).

% The dam is repaired if the cereal is cleared and a patch is used.
repaired(P) :- cleared(cereal, P), used_patch(P).

#show mystery_found/1.
#show friendship_grows/3.
#show repaired/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for cid in CHARACTERS:
        lines.append(asp.fact("character", cid))
    lines.append(asp.fact("near_dam", "prairie"))
    lines.append(asp.fact("spill", "cereal", "prairie"))
    lines.append(asp.fact("together", "bunny", "fox", "mouse", "prairie"))
    lines.append(asp.fact("cleared", "cereal", "prairie"))
    lines.append(asp.fact("used_patch", "prairie"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show mystery_found/1. #show friendship_grows/3. #show repaired/1."))
    m = set(asp.atoms(model, "mystery_found"))
    r = set(asp.atoms(model, "repaired"))
    if m and r:
        print("OK: ASP model finds the mystery and repairs the dam.")
        return 0
    print("MISMATCH: ASP model did not produce the expected story facts.")
    return 1


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    return [
        "Write a short nursery-rhyme style story about a prairie mystery involving cereal and a dam.",
        f"Tell a gentle story where {world.facts['lead'].name} and two friends solve a clue near the dam.",
        "Make the ending happy, with friendship growing after the mystery is solved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    lead: Entity = world.facts["lead"]
    h1: Entity = world.facts["helper1"]
    h2: Entity = world.facts["helper2"]
    qas = [
        QAItem(
            question=f"What mystery did {lead.name} find on the prairie?",
            answer=f"{lead.name} found spilled cereal near the dam, and that strange trail became a mystery to solve.",
        ),
        QAItem(
            question=f"Who helped {lead.name} search for clues?",
            answer=f"{h1.name} and {h2.name} helped {lead.name} search carefully and solve the prairie mystery together.",
        ),
        QAItem(
            question="What fixed the dam in the end?",
            answer=f"They used sticky clay as a patch, swept away the cereal, and the little dam stopped leaking.",
        ),
        QAItem(
            question="How did the friends feel at the end?",
            answer="They felt relieved and happy, because the mystery was solved and their friendship grew stronger.",
        ),
    ]
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a prairie?",
            answer="A prairie is a wide open grassland with lots of sky above it.",
        ),
        QAItem(
            question="What is cereal?",
            answer="Cereal is a breakfast food made from crunchy grains, usually eaten in a bowl with milk.",
        ),
        QAItem(
            question="What is a dam?",
            answer="A dam is a barrier that helps hold back water.",
        ),
        QAItem(
            question="Why do friends help solve mysteries?",
            answer="Friends help because two or more careful minds can notice more clues and solve problems together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Prairie cereal dam mystery story world.")
    ap.add_argument("--place", choices=PLACE_REGISTRY, default=None)
    ap.add_argument("--mystery", choices=MYSTERY_REGISTRY, default=None)
    ap.add_argument("--lead", choices=CHARACTER_REGISTRY, default=None)
    ap.add_argument("--helper1", choices=CHARACTER_REGISTRY, default=None)
    ap.add_argument("--helper2", choices=CHARACTER_REGISTRY, default=None)
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
    place = args.place or rng.choice(PLACE_REGISTRY)
    mystery = args.mystery or rng.choice(MYSTERY_REGISTRY)

    if args.lead and args.helper1 and args.helper2:
        if len({args.lead, args.helper1, args.helper2}) < 3:
            raise StoryError("Lead and helpers must be three different characters.")
    lead = args.lead or "bunny"
    helper1 = args.helper1 or "fox"
    helper2 = args.helper2 or "mouse"
    if len({lead, helper1, helper2}) < 3:
        lead, helper1, helper2 = "bunny", "fox", "mouse"
    return StoryParams(place=place, mystery=mystery, lead=lead, helper1=helper1, helper2=helper2)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print()
        print("--- world trace ---")
        w = sample.world
        for ent in [*w.characters.values(), *w.tools.values()]:
            print(f"{ent.id}: meters={dict(ent.meters)} memes={dict(ent.memes)}")
        print(f"facts={w.facts}")
    if qa:
        print()
        print(format_qa(sample))


def curated_params() -> list[StoryParams]:
    return [StoryParams(place="prairie", mystery="cereal_dam", lead="bunny", helper1="fox", helper2="mouse")]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show mystery_found/1. #show friendship_grows/3. #show repaired/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show mystery_found/1. #show friendship_grows/3. #show repaired/1."))
        print("mystery_found:", sorted(set(asp.atoms(model, "mystery_found"))))
        print("friendship_grows:", sorted(set(asp.atoms(model, "friendship_grows"))))
        print("repaired:", sorted(set(asp.atoms(model, "repaired"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for p in curated_params():
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < max(1, args.n) and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
