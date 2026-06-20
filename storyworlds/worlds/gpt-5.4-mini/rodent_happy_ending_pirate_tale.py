#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/rodent_happy_ending_pirate_tale.py
===================================================================

A standalone storyworld for a tiny pirate-style tale with a rodent and a
happy ending. The world is small and classical: a pretend pirate crew on a
dockside boat, a curious rodent in the hold, a little mistake, a calm fix, and
an ending image that proves the crew and the rodent are both safe.

The story model uses typed entities with physical meters and emotional memes,
and it renders prose from simulated state rather than swapping nouns into a
frozen paragraph.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/rodent_happy_ending_pirate_tale.py
    python storyworlds/worlds/gpt-5.4-mini/rodent_happy_ending_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4-mini/rodent_happy_ending_pirate_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/rodent_happy_ending_pirate_tale.py --trace
    python storyworlds/worlds/gpt-5.4-mini/rodent_happy_ending_pirate_tale.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # character | thing
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    friendly: bool = False
    rodent: bool = False
    collectible: bool = False
    safe_snack: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Scene:
    id: str
    place: str
    rig: str
    goal: str
    dark_spot: str
    pirate_word: str
    send_off: str


@dataclass
class Rodent:
    id: str
    label: str
    kind: str
    size: str
    nuzzle: str
    nibble: str
    avoid: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    shiny: str
    carry: str
    vulnerable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_startle(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["startled"] < THRESHOLD:
            continue
        sig = ("startle", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for ch in world.entities.values():
            if ch.kind == "character":
                ch.memes["alarm"] += 1
        out.append("__alarm__")
    return out


CAUSAL_RULES = [Rule("startle", "social", _r_startle)]


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


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= 2]


def hazard_at_risk(rodent: Rodent, treasure: Treasure) -> bool:
    return treasure.vulnerable and rodent.kind == "rodent"


def gentle_fix_ok(fix: Fix) -> bool:
    return fix.sense >= 2


def choose_fix() -> Fix:
    return max(FIXES.values(), key=lambda f: f.sense)


def tell(scene: Scene, rodent: Rodent, treasure: Treasure, fix: Fix,
         hero: str = "Mina", hero_gender: str = "girl",
         mate: str = "Jasper", mate_gender: str = "boy",
         parent_type: str = "mother",
         trap_delay: int = 0,
         rodent_name: str = "Nib", rodent_friendly: bool = True) -> World:
    world = World()
    h = world.add(Entity(id=hero, kind="character", type=hero_gender, role="captain",
                         traits=["bold"], attrs={"scene": scene.id}))
    m = world.add(Entity(id=mate, kind="character", type=mate_gender, role="mate",
                         traits=["thoughtful"], attrs={"scene": scene.id}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type,
                              role="parent", label="the parent"))
    r = world.add(Entity(id=rodent_name, kind="character", type="thing", label=rodent.label,
                         rodent=True, friendly=rodent_friendly))
    t = world.add(Entity(id="treasure", type="thing", label=treasure.label,
                         collectible=True))
    world.facts.update(scene=scene, rodent_cfg=rodent, treasure_cfg=treasure,
                       fix=fix, hero=h, mate=m, parent=parent, rodent=r, treasure=t,
                       trap_delay=trap_delay)
    h.memes["bravery"] = 6.0
    m.memes["care"] = 5.0
    r.memes["curiosity"] = 4.0
    r.memes["hunger"] = 3.0
    world.say(
        f"At dusk, {h.id} and {m.id} turned the little deck into {scene.place}. "
        f"{scene.rig}"
    )
    world.say(
        f'"{scene.pirate_word} {h.id} and {scene.pirate_word.lower()} {m.id}!" '
        f"{h.id} shouted. \"Let's find {scene.goal}!\""
    )
    world.para()
    world.say(
        f"But the {scene.dark_spot} was dim, and that was where a small rodent "
        f"had crept in, drawn by the smell of crumbs."
    )
    world.say(f'{m.id} peered toward the hold. "We need to be gentle," {m.id} said.')
    h.memes["want"] += 1
    world.say(
        f'{h.id} leaned closer and spotted {rodent_name}, a tiny rodent with '
        f"{rodent.nibble} little whiskers. \"I know! We'll chase it away!\""
    )
    world.say(f'{m.id} bit {m.pronoun("possessive")} lip. "Not so fast. It looks scared."')
    world.para()
    if trap_delay:
        h.meters["rush"] += 1
        world.say(
            f"{h.id} hurried to grab a crate lid, but {m.id} touched {h.pronoun('possessive')} arm "
            f"and pointed at the rodent's trembling nose."
        )
    if rodent_friendly:
        world.say(
            f"Instead of a noisy chase, {m.id} sprinkled a few safe crumbs near the "
            f"open hatch and set down a little wooden bowl of water."
        )
        world.say(
            f"{rodent_name} sniffed, twitched {rodent.nuzzle}, and stayed still."
        )
        world.say(
            f"{h.id} lifted a lantern and guided the light toward the dock, not at the "
            f"rodent. The little animal followed the crumbs and slipped through the "
            f"side gate toward the harbor weeds."
        )
        r.meters["safe"] += 1
        t.meters["saved"] += 1
        h.memes["kindness"] += 1
        m.memes["relief"] += 1
        world.say(
            f"Before long, the rodent was back in the grass, and the pirates were "
            f"back on deck, smiling at the quiet water."
        )
        world.say(
            f'Then {parent.label_word.capitalize()} came by with a warm blanket and '
            f"said, \"A brave crew is gentle when it can be.\""
        )
        world.say(
            f"{h.id} and {m.id} nodded. They kept their treasure safe, and the little "
            f"rodent found its home without anyone getting hurt."
        )
    else:
        world.say(
            f"The rodent darted under the boardwalk, and the crew slowed down, "
            f"choosing patience over noise. In the end, it slipped away safely "
            f"on its own."
        )
    world.facts["outcome"] = "happy"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scene, rodent, treasure = f["scene"], f["rodent_cfg"], f["treasure_cfg"]
    return [
        f'Write a pirate-style story for a 3-to-5-year-old that includes the word "{rodent.label}" and ends happily.',
        f"Tell a gentle pirate tale where {f['hero'].id} and {f['mate'].id} see a {rodent.label} near the treasure and choose a kind solution.",
        f'Write a short happy-ending story set on {scene.place} with a tiny rodent, a lantern, and a safe ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    h, m, parent = f["hero"], f["mate"], f["parent"]
    rodent, treasure = f["rodent_cfg"], f["treasure_cfg"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {h.id}, {m.id}, {parent.label_word}, and a tiny rodent named {world.facts['rodent'].id if 'rodent' in world.facts else 'Nib'}. They all share one small pirate adventure on the deck."
        ),
        QAItem(
            question="What did the children find near the treasure?",
            answer=f"They found a small rodent near the treasure hold. It was drawn by crumbs and the smell of food, so the dark corner felt busy and surprising."
        ),
        QAItem(
            question=f"What did {m.id} suggest?",
            answer=f"{m.id} said to be gentle and not start a noisy chase. That helped the crew choose crumbs, water, and a lantern instead of panic."
        ),
        QAItem(
            question="How did the happy ending happen?",
            answer=f"The rodent followed safe crumbs to the dockside weeds and got back to a home place. The children stayed calm, kept the treasure safe, and ended the day smiling."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rodent?",
            answer="A rodent is a small animal with teeth that keep growing, so it likes to nibble food and soft things. Mice and rats are rodents."
        ),
        QAItem(
            question="Why should people be gentle with a scared animal?",
            answer="A scared animal may run, hide, or get hurt if someone shouts. Gentle hands and a calm voice help it stay safe."
        ),
        QAItem(
            question="What does a lantern do on a pirate deck?",
            answer="A lantern makes soft light so people can see in the dark. It helps the crew look around without stumbling."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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
        if e.kind:
            bits.append(f"kind={e.kind}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.rodent:
            bits.append("rodent=True")
        if e.collectible:
            bits.append("collectible=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


SCENES = {
    "dock": Scene("dock", "a pirate deck", "The sail was patched, the deck boards were warm, and a little chest held marbles instead of gold.",
                  "the lantern room", "dark hold", "Captain", "sail off into the moonlit harbor"),
    "cove": Scene("cove", "a hidden cove", "The rope swing hung from the mast, a shell map marked the shore, and a biscuit tin held the treasure.",
                  "the bilge corner", "shadowy corner", "Captain", "head home before the tide rose"),
}

RODENTS = {
    "mouse": Rodent("mouse", "mouse", "rodent", "tiny", "small nose", "nibbly crumbs", "loud footsteps", tags={"rodent"}),
    "rat": Rodent("rat", "rat", "rodent", "small", "soft whiskers", "nibbly oats", "shouting", tags={"rodent"}),
}

TREASURES = {
    "shells": Treasure("shells", "a little shell necklace", "shell necklace", "shiny", "carry in a pocket", True, tags={"treasure"}),
    "coin": Treasure("coin", "a bright brass coin", "brass coin", "shiny", "carry in a pouch", True, tags={"treasure"}),
}

FIXES = {
    "crumbs": Fix("crumbs", 3, 3, "sprinkled safe crumbs and waited with a lantern until the rodent could slip away",
                  "sprinkled crumbs, but the plan was too hurried and the rodent ran in circles",
                  "sprinkled safe crumbs and waited with a lantern", tags={"gentle", "rodent"}),
    "gate": Fix("gate", 2, 2, "opened the little side gate and let the rodent leave by itself",
                "opened the gate, but the rodent was too startled to move",
                "opened the little side gate and let the rodent leave", tags={"gentle"}),
}


@dataclass
class StoryParams:
    scene: str
    rodent: str
    treasure: str
    fix: str
    hero: str
    hero_gender: str
    mate: str
    mate_gender: str
    parent: str
    trap_delay: int = 0
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SCENES:
        for r in RODENTS:
            for t in TREASURES:
                if hazard_at_risk(RODENTS[r], TREASURES[t]):
                    combos.append((s, r, t))
    return combos


KNOWLEDGE = {
    "rodent": [("What is a rodent?",
                "A rodent is a small animal with teeth that keep growing, so it likes to nibble food and soft things. Mice and rats are rodents.")],
    "treasure": [("What is treasure?",
                 "Treasure is something special people keep safe because it is valuable or important to them.")],
    "lantern": [("What does a lantern do?",
                "A lantern gives soft light so people can see in the dark without stumbling.")],
    "gentle": [("Why should people be gentle with a scared animal?",
               "A scared animal may run, hide, or get hurt if someone shouts. Gentle hands and a calm voice help it stay safe.")],
}


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for rid in RODENTS:
        lines.append(asp.fact("rodent", rid))
    for tid in TREASURES:
        lines.append(asp.fact("treasure", tid))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, f.sense))
        lines.append(asp.fact("power", fid, f.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
hazard(R, T) :- rodent(R), treasure(T).
sensible(F) :- fix(F), sense(F, S), sense_min(M), S >= M.
valid(S, R, T) :- scene(S), rodent(R), treasure(T), hazard(R, T).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    if set(asp_sensible()) == {f.id for f in sensible_fixes()}:
        print("OK: sensible fixes match.")
    else:
        rc = 1
        print("MISMATCH in sensible fixes.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: smoke-test generation succeeded.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate-style happy-ending rodent storyworld.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--rodent", choices=RODENTS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--mate")
    ap.add_argument("--mate-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid pirate-rodent combinations.")
    scene, rodent, treasure = rng.choice(sorted(
        c for c in combos
        if (args.scene is None or c[0] == args.scene)
        and (args.rodent is None or c[1] == args.rodent)
        and (args.treasure is None or c[2] == args.treasure)
    ))
    if args.fix and not gentle_fix_ok(FIXES[args.fix]):
        raise StoryError("That fix is too rough for a happy ending.")
    fix = args.fix or rng.choice(sorted(sensible_fixes(), key=lambda f: f.id)).id
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    mate_gender = args.mate_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(["Mina", "Rae", "Toby", "Nell", "Finn"])
    mate = args.mate or rng.choice(["Jasper", "Pip", "Milo", "June", "Kit"])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(scene, rodent, treasure, fix, hero, hero_gender, mate, mate_gender, parent)


def generation_prompts_for(sample_world: World) -> list[str]:
    return generation_prompts(sample_world)


def generate(params: StoryParams) -> StorySample:
    world = tell(SCENES[params.scene], RODENTS[params.rodent], TREASURES[params.treasure],
                 FIXES[params.fix], params.hero, params.hero_gender, params.mate,
                 params.mate_gender, params.parent, params.trap_delay)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts_for(world),
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible fixes: {', '.join(asp_sensible())}\n")
        for s, r, t in asp_valid_combos():
            print(f"  {s:8} {r:8} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams("dock", "mouse", "shells", "crumbs", "Mina", "girl", "Jasper", "boy", "mother")),
                   generate(StoryParams("cove", "rat", "coin", "gate", "Toby", "boy", "June", "girl", "father"))]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} & {p.mate}: {p.rodent} near {p.treasure} ({p.scene})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
