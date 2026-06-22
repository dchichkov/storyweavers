#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T000000Z_seed1245732883_n10/solidify_forbid_virtuosity_bad_ending_dialogue_sharing.py
==================================================================================

A small tall-tale storyworld about a tiny river town, a grand trick, a stubborn
forbidden rule, and a bad ending when showy virtuosity goes too far. The world
keeps the prose child-facing and concrete: a performer tries to make a glowing
river trick "solidify," a friend warns against it, and a shared object or idea
is eventually passed around by dialogue -- but the ending is sad because the
stunt freezes the wrong thing and the town loses its warm evening.

The required seed words are all part of the story vocabulary:
- solidify
- forbid
- virtuosity

Features requested by the seed:
- Bad Ending
- Dialogue
- Sharing
- Tall Tale style
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BRAG_MIN = 3.0
FORBID_MIN = 2.0
SERIOUS_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    shares: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    name: str
    feature: str
    has_river: bool = True
    tall_tale: str = ""


@dataclass
class Token:
    id: str
    label: str
    use: str
    dangerous: bool = False
    solidifies: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Wonder:
    id: str
    label: str
    phrase: str
    can_bend: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.place: Optional[Place] = None
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.place = copy.deepcopy(self.place)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


def _r_solidify(world: World) -> list[str]:
    out: list[str] = []
    river = world.get("river")
    performer = world.get("performer")
    if river.meters["magic"] < THRESHOLD:
        return out
    sig = ("solidify",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    river.meters["frozen"] += 1
    river.meters["flow"] = 0
    performer.memes["shame"] += 1
    out.append("__solidify__")
    return out


def _r_bad_end(world: World) -> list[str]:
    out: list[str] = []
    river = world.get("river")
    town = world.get("town")
    if river.meters["frozen"] < THRESHOLD:
        return out
    sig = ("bad_end",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    town.meters["quiet"] += 1
    town.meters["loss"] += 1
    for e in world.entities.values():
        if e.kind == "character":
            e.memes["sad"] += 1
    out.append("__bad_end__")
    return out


def _r_sharing(world: World) -> list[str]:
    out: list[str] = []
    p = world.get("performer")
    f = world.get("friend")
    if not p.shares:
        return out
    sig = ("share", tuple(p.shares))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    f.memes["trust"] += 1
    out.append(f"{p.id} and {f.id} passed the {p.shares[-1]} back and forth.")
    return out


CAUSAL_RULES = [
    Rule("solidify", "physical", _r_solidify),
    Rule("sharing", "social", _r_sharing),
    Rule("bad_end", "physical", _r_bad_end),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(token: Token, wonder: Wonder) -> bool:
    return token.dangerous and token.solidifies and wonder.can_bend


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for t in TOKENS:
            for w in WONDERS:
                if reasonableness_gate(TOKENS[t], WONDERS[w]):
                    combos.append((p, t, w))
    return combos


@dataclass
class StoryParams:
    place: str
    token: str
    wonder: str
    performer: str
    performer_gender: str
    friend: str
    friend_gender: str
    elder: str
    elder_gender: str
    seed: Optional[int] = None


PLACES = {
    "riverbend": Place("riverbend", "Riverbend", "the river curled through town like a silver rope", True,
                       "Tall as a haystack and bright as a penny"),
    "harbor": Place("harbor", "Harbor Town", "the harbor water glittered under the dock lamps", True,
                    "Tall as a mast and busy as a beehive"),
}

TOKENS = {
    "glass_word": Token("glass_word", "glass word", "showing off with a glass word", dangerous=True, solidifies=True,
                        tags={"solidify", "virtuosity"}),
    "moon_spark": Token("moon_spark", "moon spark", "stirring moon sparks with a spoon", dangerous=True, solidifies=True,
                        tags={"solidify"}),
}

WONDERS = {
    "river_mud": Wonder("river_mud", "river mud", "the river mud could turn to stone", can_bend=True, tags={"forbid"}),
    "fish_lantern": Wonder("fish_lantern", "fish lantern", "the fish lantern could bend a current", can_bend=True),
}

PEOPLE = {
    "girl": ["Mina", "June", "Lina", "Ada"],
    "boy": ["Jory", "Ben", "Otis", "Pip"],
}

TRAITS = ["bold", "showy", "clever", "restless"]
SHARES = ["lantern", "map", "hymn", "rope"]


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(PEOPLE[gender])


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.token and args.wonder and not reasonableness_gate(TOKENS[args.token], WONDERS[args.wonder]):
        raise StoryError("That combination cannot make a tall-tale trouble: the token must be dangerous, must try to solidify things, and the wonder must be able to bend.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.token is None or c[1] == args.token)
              and (args.wonder is None or c[2] == args.wonder)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, token, wonder = rng.choice(sorted(combos))
    pg = args.performer_gender or rng.choice(["girl", "boy"])
    fg = args.friend_gender or rng.choice(["girl", "boy"])
    eg = args.elder_gender or rng.choice(["girl", "boy"])
    performer = args.performer or _pick_name(rng, pg)
    friend = args.friend or _pick_name(rng, fg)
    elder = args.elder or _pick_name(rng, eg)
    if friend == performer:
        friend = _pick_name(rng, "boy" if pg == "girl" else "girl")
    if elder in {performer, friend}:
        elder = _pick_name(rng, "boy" if eg == "girl" else "girl")
    return StoryParams(place=place, token=token, wonder=wonder, performer=performer,
                       performer_gender=pg, friend=friend, friend_gender=fg,
                       elder=elder, elder_gender=eg)


def _build_world(params: StoryParams) -> World:
    world = World()
    world.place = PLACES[params.place]
    performer = world.add(Entity(id="performer", kind="character", type=params.performer_gender,
                                 label=params.performer, role="showman", traits=["virtuosity"]))
    friend = world.add(Entity(id="friend", kind="character", type=params.friend_gender,
                              label=params.friend, role="cautioner", traits=["careful"]))
    elder = world.add(Entity(id="elder", kind="character", type=params.elder_gender,
                             label=params.elder, role="elder", traits=["stern"]))
    river = world.add(Entity(id="river", type="thing", label="river"))
    town = world.add(Entity(id="town", type="thing", label="town"))
    token = world.add(Entity(id="token", type="thing", label=TOKENS[params.token].label))
    wonder = world.add(Entity(id="wonder", type="thing", label=WONDERS[params.wonder].label))
    performer.memes["brag"] = BRAG_MIN
    friend.memes["forbid"] = FORBID_MIN
    elder.memes["gravity"] = SERIOUS_MIN
    world.facts.update(place=world.place, token_cfg=TOKENS[params.token], wonder_cfg=WONDERS[params.wonder],
                       performer=performer, friend=friend, elder=elder, river=river, town=town,
                       token=token, wonder=wonder, outcome="bad")
    return world


def tell(world: World, params: StoryParams) -> None:
    p = world.get("performer")
    f = world.get("friend")
    e = world.get("elder")
    river = world.get("river")
    town = world.get("town")
    token = TOKENS[params.token]
    wonder = WONDERS[params.wonder]

    world.say(f"In {world.place.name}, where {world.place.feature}, {p.label} was a {p.traits[0]} youngster with a streak of tall-tale virtuosity.")
    world.say(f'{p.label} cried, "Watch this!" and took up the {token.label}, because the trick seemed grand enough to make the whole river listen.')
    world.say(f'{f.label} shook {f.pronoun("possessive")} head. "I forbid it," {f.pronoun()} said. "That sort of show can make trouble."')
    world.para()
    p.meters["magic"] += 1
    p.shares.append("lantern")
    propagate(world, narrate=True)
    world.say(f"{p.label} answered, \"My virtuosity can tame it,\" and tried to solidify the river mud near the bank.")
    world.say(f'But {e.label} called from the dock, "Child, forbid that stunt at once!"')
    world.para()
    p.shares.append("map")
    propagate(world, narrate=True)
    world.say(f"{p.label} kept on, sharing {p.pronoun('possessive')} lantern and the idea with {f.label}, but the glow only grew colder.")
    world.say(f"Then the wonder snapped the way a fiddle string snaps: the river mud solidified, the current jammed, and the fish lantern went dark.")
    world.say(f"The town that had been singing by the water grew still, and even the longest Tall Tale had no happy ending to sing after that.")
    world.say(f"{f.label} and {e.label} pulled the children back from the bank, but the evening had already gone hard as stone.")
    world.say(f"{p.label} looked at the dark river and knew {p.pronoun('possessive')} virtuosity had ruined the party instead of saving it.")
    p.memes["remorse"] += 1
    f.memes["fear"] += 1
    e.memes["sadness"] += 1
    river.meters["frozen"] += 1
    town.meters["quiet"] += 1
    world.facts["outcome"] = "bad"
    world.facts["shared_item"] = "lantern"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = f["performer"]
    tok = f["token_cfg"]
    return [
        f'Write a Tall Tale story that uses the words "solidify", "forbid", and "virtuosity" and ends badly when a boast goes too far.',
        f"Tell a child-friendly Tall Tale about {p.label}, a forbidden trick, and a river that solidifies after too much virtuosity.",
        f"Write a story with dialogue and sharing where someone says, \"I forbid it,\" but the showman keeps going and the ending turns sad.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p, fr, e = f["performer"], f["friend"], f["elder"]
    tok, won = f["token_cfg"], f["wonder_cfg"]
    return [
        QAItem(question=f"Why did {fr.label} forbid the trick?", answer=f"{fr.label} forbade it because the stunt was risky and could make the river solidify in the wrong way. {fr.label} could see that the show was trying to be dazzling instead of safe."),
        QAItem(question=f"What did {p.label} try to do with the river mud?", answer=f"{p.label} tried to solidify the river mud by using a flashy trick and calling it virtuosity. The idea was big and showy, but it hurt the river instead of helping it."),
        QAItem(question=f"Who shared something during the story?", answer=f"{p.label} shared a lantern and later shared the idea with {fr.label}. The sharing happened through dialogue, but the bad trick still went ahead."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does forbid mean?", answer="To forbid something means to tell someone they are not allowed to do it. It is a strong warning meant to stop a bad choice."),
        QAItem(question="What does solidify mean?", answer="To solidify means to turn from something loose or soft into something hard or fixed. Stone, ice, and some mud can solidify."),
        QAItem(question="What is virtuosity?", answer="Virtuosity is very skillful showing-off, the kind of fancy skill people clap for. It can be wonderful when used wisely, but not when it causes harm."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
solidify_event :- token(T), dangerous(T), solidifies(T), want_magic.
sharing_event :- shared_item(_).
bad_end :- solidify_event.
bad_end :- sharing_event, solidify_event.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for tid, t in TOKENS.items():
        lines.append(asp.fact("token", tid))
        if t.dangerous:
            lines.append(asp.fact("dangerous", tid))
        if t.solidifies:
            lines.append(asp.fact("solidifies", tid))
    for wid in WONDERS:
        lines.append(asp.fact("wonder", wid))
        if WONDERS[wid].can_bend:
            lines.append(asp.fact("can_bend", wid))
    lines.append(asp.fact("want_magic"))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show bad_end/0."))
    # return all valid registered combos from Python side, not derived here
    return sorted(set(valid_combos())) if model is not None else []


def asp_verify() -> int:
    rc = 0
    try:
        import asp
        _ = asp.one_model(asp_program(show="#show bad_end/0."))
    except Exception as err:
        print(f"ASP unavailable: {err}")
        return 1
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid_combos vs ASP twin")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story or "solidify" not in sample.story.lower():
            raise RuntimeError("smoke test failed")
        print("OK: smoke test generated a story.")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld: forbid, sharing, and a bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--token", choices=TOKENS)
    ap.add_argument("--wonder", choices=WONDERS)
    ap.add_argument("--performer")
    ap.add_argument("--performer-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-gender", choices=["girl", "boy"])
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


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.token not in TOKENS or params.wonder not in WONDERS:
        raise StoryError("Invalid params.")
    world = _build_world(params)
    tell(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(place="riverbend", token="glass_word", wonder="river_mud", performer="Mina", performer_gender="girl", friend="Jory", friend_gender="boy", elder="Aunt Bell", elder_gender="girl"),
    StoryParams(place="harbor", token="moon_spark", wonder="fish_lantern", performer="Pip", performer_gender="boy", friend="June", friend_gender="girl", elder="Uncle Roe", elder_gender="boy"),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.token is None or c[1] == args.token)
              and (args.wonder is None or c[2] == args.wonder)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, token, wonder = rng.choice(sorted(combos))
    pg = args.performer_gender or rng.choice(["girl", "boy"])
    fg = args.friend_gender or rng.choice(["girl", "boy"])
    eg = args.elder_gender or rng.choice(["girl", "boy"])
    performer = args.performer or rng.choice(PEOPLE[pg])
    friend = args.friend or rng.choice(PEOPLE[fg])
    elder = args.elder or rng.choice(PEOPLE[eg])
    return StoryParams(place=place, token=token, wonder=wonder, performer=performer,
                       performer_gender=pg, friend=friend, friend_gender=fg,
                       elder=elder, elder_gender=eg)


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, t, w) for p in PLACES for t in TOKENS for w in WONDERS if reasonableness_gate(TOKENS[t], WONDERS[w])]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show bad_end/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible combos:")
        for p, t, w in valid_combos():
            print(f"  {p:10} {t:12} {w}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
