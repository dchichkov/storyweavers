#!/usr/bin/env python3
"""
A standalone Storyweavers world: a small whodunit set in a craft workshop.

Premise:
- In a cozy craft workshop, a prized quote card disappears during a busy afternoon.
- A gluttonous squirrel-like helper keeps sneaking snacks from the supply table.
- The hero's inner monologue helps them notice clues.
- Teamwork solves the mystery and restores the missing quote.

This script follows the Storyworld contract:
- standalone stdlib Python
- lazy ASP import for verification/query modes
- world simulation with physical meters and emotional memes
- StorySample/QAItem/StoryError from storyworlds.results
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

THEME = "craft workshop"
SEED_WORDS = {"quote", "glutton"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["lost", "sticky", "crumbs", "ink", "dust"]:
            self.meters.setdefault(k, 0.0)
        for k in ["worry", "joy", "curiosity", "doubt", "teamwork", "pride", "hunger"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    name: str = "Mina"
    sidekick: str = "Toby"
    culprit: str = "Chipper"
    seed: Optional[int] = None


@dataclass
class World:
    hero: Entity
    sidekick: Entity
    culprit: Entity
    quote_card: Entity
    teacup: Entity
    craft_table: Entity
    note_board: Entity
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _new_entity(eid: str, kind: str, type_: str, label: str, phrase: str = "", **kwargs) -> Entity:
    return Entity(id=eid, kind=kind, type=type_, label=label, phrase=phrase, **kwargs)


def build_world(params: StoryParams) -> World:
    hero = _new_entity(params.name, "character", "girl", "the maker", meters={}, memes={})
    sidekick = _new_entity(params.sidekick, "character", "boy", "the helper", meters={}, memes={})
    culprit = _new_entity(params.culprit, "character", "animal", "the glutton", meters={}, memes={})
    quote_card = _new_entity("quote_card", "thing", "card", "quote card", 'a neat card with a quote on it')
    teacup = _new_entity("teacup", "thing", "cup", "tea cup", "a tiny cup of tea")
    craft_table = _new_entity("table", "thing", "table", "craft table", "the long craft table")
    note_board = _new_entity("board", "thing", "board", "notice board", "the cork board by the window")
    world = World(hero, sidekick, culprit, quote_card, teacup, craft_table, note_board)
    world.facts["theme"] = THEME
    return world


def _inner_monologue(world: World, hero: Entity, clue: str) -> None:
    hero.memes["curiosity"] += 1
    hero.memes["doubt"] += 1
    world.say(f'In {hero.pronoun("possessive")} head, {hero.id} thought, "{clue}"')


def _teamwork(world: World, hero: Entity, sidekick: Entity) -> None:
    hero.memes["teamwork"] += 1
    sidekick.memes["teamwork"] += 1
    hero.memes["joy"] += 1
    sidekick.memes["joy"] += 1


def tell(params: StoryParams) -> World:
    world = build_world(params)
    h, s, c = world.hero, world.sidekick, world.culprit
    q, t, table, board = world.quote_card, world.teacup, world.craft_table, world.note_board

    h.memes["worry"] += 1
    s.memes["pride"] += 1
    c.memes["hunger"] += 2
    q.hidden_in = "behind the paint jars"
    q.meters["lost"] = 1
    t.meters["crumbs"] = 2
    t.meters["sticky"] = 1
    c.carried_by = None

    world.say(
        f"In the {THEME}, {h.id} was arranging paper stars when {h.pronoun('possessive')} "
        f"best helper, {s.id}, noticed something strange: the shiny {q.label} was gone."
    )
    world.say(
        f"On the table sat a {t.label}, and beside it there were crumbs shaped like tiny claws."
    )

    world.para()
    _inner_monologue(world, h, "A missing quote, crumbs, and sticky glue? This feels like a real mystery.")
    world.say(
        f"{h.id} looked at the board, the jars, and the floorboards, as if the room itself might answer."
    )
    world.say(
        f"{c.id}, a glutton with a very round belly, was licking a jam smudge from one paw and trying to look innocent."
    )

    world.para()
    world.say(
        f"{s.id} whispered, 'Maybe the quote card blew away.' But {h.id} shook {h.pronoun('possessive')} head."
    )
    world.say(
        f"The clue trail pointed to the snack shelf, not the window. {h.id} noticed jam on the table leg."
    )
    _inner_monologue(world, h, "The glutton went for snacks first. Maybe the missing card is hidden nearby.")
    world.say(
        f"{h.id} asked {s.id} to peek under the table while {h.id} checked behind the paint jars."
    )

    world.para()
    if q.hidden_in == "behind the paint jars":
        q.hidden_in = None
        q.carried_by = h.id
        q.meters["lost"] = 0
        world.say(
            f"There it was: the {q.label}, tucked behind the paint jars, with a little sticky thumbprint on the corner."
        )
    world.say(
        f"{s.id} found a trail of sugar dust leading straight to {c.id}'s snack tin."
    )
    world.say(
        f"{c.id} drooped and admitted, 'I only wanted one more cookie, then I bumped the card by accident.'"
    )

    world.para()
    _teamwork(world, h, s)
    world.say(
        f"{h.id} did not scold. Instead, {h.id} handed {c.id} a napkin and said, "
        f"'Let's clean the mess together, and then you can help hang the quote where everyone can read it.'"
    )
    world.say(
        f"{s.id} wiped the sticky corner, {c.id} held the board steady, and {h.id} pinned the quote card in the center."
    )
    world.say(
        f"In the end, the workshop felt calm again: the mystery was solved, the quote was safe, and the glutton had a full snack and a useful job."
    )

    world.facts.update(
        hero=h, sidekick=s, culprit=c, quote=q, teacup=t, table=table, board=board,
        resolved=True, culprit_hunger=c.memes["hunger"], teamwork=h.memes["teamwork"],
        clue="crumbs and sticky glue",
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    h, s, c, q = world.facts["hero"], world.facts["sidekick"], world.facts["culprit"], world.facts["quote"]
    return [
        QAItem(
            question=f"What mystery did {h.id} notice in the {THEME}?",
            answer=f"{h.id} noticed that the {q.label} was missing, along with crumbs and sticky glue that made the room feel suspicious.",
        ),
        QAItem(
            question=f"Who turned out to be the glutton in the story?",
            answer=f"{c.id} turned out to be the glutton. {c.id} had been sneaking snacks and accidentally bumped the quote card.",
        ),
        QAItem(
            question=f"How did {h.id} and {s.id} solve the problem together?",
            answer=f"They searched the room as a team, found the quote card behind the paint jars, cleaned the sticky corner, and pinned it back on the board.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quote?",
            answer="A quote is a line that someone said or wrote down, often because it sounds wise, funny, or important.",
        ),
        QAItem(
            question="What does glutton mean?",
            answer="A glutton is someone who wants to eat much more than they need, usually very eagerly.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and share the work so a job gets done better and faster.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet talking a character does inside their own mind while they think things through.",
        ),
        QAItem(
            question="What is a craft workshop?",
            answer="A craft workshop is a place where people make art, build little projects, and use things like paper, glue, and paint.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a child-friendly whodunit set in a {THEME} about a missing quote card and a glutton who loves snacks.",
        "Tell a short mystery story where the hero's inner monologue helps solve the clue trail, and teamwork fixes the mess.",
        f"Create a gentle detective story that includes the words '{next(iter(SEED_WORDS))}' and '{sorted(SEED_WORDS)[1]}'.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in [world.hero, world.sidekick, world.culprit, world.quote_card, world.teacup, world.craft_table, world.note_board]:
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A story is valid when the setting is the craft workshop and the plot includes
% both the quote card and the glutton.
setting(craft_workshop).
requires(craft_workshop, quote).
requires(craft_workshop, glutton).

valid_story(S) :- setting(S), requires(S, quote), requires(S, glutton).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy import
    return "\n".join(
        [
            asp.fact("setting", "craft_workshop"),
            asp.fact("requires", "craft_workshop", "quote"),
            asp.fact("requires", "craft_workshop", "glutton"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp  # lazy import
    models = asp.one_model(asp_program("#show valid_story/1."))
    ok = any(atom.name == "valid_story" for atom in models)
    if ok:
        print("OK: ASP rules recognize the craft workshop story domain.")
        return 0
    print("MISMATCH: ASP rules failed to recognize the story domain.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit story world set in a craft workshop.")
    ap.add_argument("--name", default=None)
    ap.add_argument("--sidekick", default=None)
    ap.add_argument("--culprit", default=None)
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
    name = args.name or rng.choice(["Mina", "Tess", "Ivy", "June", "Pia"])
    sidekick = args.sidekick or rng.choice(["Toby", "Luca", "Ned", "Owen", "Ben"])
    culprit = args.culprit or rng.choice(["Chipper", "Nib", "Pip", "Morsel"])
    if name == sidekick:
        raise StoryError("The hero and sidekick must be different characters.")
    if culprit in {name, sidekick}:
        raise StoryError("The culprit must be different from the hero and sidekick.")
    return StoryParams(name=name, sidekick=sidekick, culprit=culprit, seed=args.seed)


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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(name="Mina", sidekick="Toby", culprit="Chipper"),
    StoryParams(name="Ivy", sidekick="Luca", culprit="Nib"),
    StoryParams(name="June", sidekick="Owen", culprit="Pip"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print("ASP model:", [str(a) for a in model])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
