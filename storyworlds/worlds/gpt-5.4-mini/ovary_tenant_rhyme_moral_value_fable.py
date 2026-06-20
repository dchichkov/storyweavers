#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/ovary_tenant_rhyme_moral_value_fable.py
======================================================================

A small fable-world about a tenant in a garden room, a tender ovary on a blossom,
and a moral about gentle care.  The story is built from a tiny simulation: a
tenant wants something shiny from the garden, a wiser helper warns that rough
hands can spoil what is still growing, and the ending proves the change with a
sweet, safe image.

This world keeps a fable-like shape, includes a light rhyme cadence, and exposes
the shared Storyweavers interface plus a Python/ASP parity check.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    season: str
    mood: str


@dataclass
class Tool:
    id: str
    label: str
    sharp: bool = False
    gentle: bool = False


@dataclass
class Blossom:
    id: str
    label: str
    the: str
    near: str
    delicate: bool = True
    fruits_from: bool = True


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_damage(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["hurt"] < THRESHOLD:
            continue
        sig = ("hurt", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["bruise"] += 1
        out.append("__hurt__")
    return out


CAUSAL_RULES = [Rule("damage", "physical", _r_damage)]


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


def reasonableness_gate(tool: Tool, blossom: Blossom) -> bool:
    return tool.sharp and blossom.delicate


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def injury_severity(delay: int) -> int:
    return 1 + delay


def contained(response: Response, delay: int) -> bool:
    return response.power >= injury_severity(delay)


def predict_damage(world: World, blossom_id: str) -> dict:
    sim = world.copy()
    _do_wrong(sim, sim.get("tool"), narrate=False)
    b = sim.get(blossom_id)
    return {"hurt": b.meters["hurt"] >= THRESHOLD, "bruise": b.meters["bruise"]}


def _do_wrong(world: World, tool: Entity, narrate: bool = True) -> None:
    target = world.get("ovary")
    target.meters["hurt"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, tenant: Entity, keeper: Entity, setting: Setting, blossom: Blossom) -> None:
    tenant.memes["curiosity"] += 1
    world.say(
        f"In {setting.place}, where the {setting.mood} breeze could barely sing, "
        f"{tenant.id} was a tenant with a tiny room to keep. "
        f"The room had a window, a pot of mint, and a {blossom.label} by the sill."
    )
    world.say(
        f'"The night is bright, the path is long," {tenant.id} rhymed with a grin. '
        f'"A little light would make my chores feel like a song."'
    )


def want_shiny(world: World, tenant: Entity, tool: Tool) -> None:
    tenant.memes["want"] += 1
    world.say(
        f"{tenant.id} spotted {tool.label} on the shelf and leaned in close. "
        f'"If I tap the bud, I will know if it is ripe," {tenant.id} said, '
        f"though the idea was not wise."
    )


def warn(world: World, keeper: Entity, tenant: Entity, blossom: Blossom) -> None:
    pred = predict_damage(world, "ovary")
    keeper.memes["care"] += 1
    world.facts["predicted_hurt"] = pred["hurt"]
    world.say(
        f'"Gently, gently," said {keeper.id}. "That {blossom.label} holds an {blossom.label_word} inside. '
        f'If you poke it rough, the growing part may bruise."'
    )
    if pred["hurt"]:
        world.say(f'"A bruise can spoil the bloom," {keeper.id} warned, "and no sweet fruit will come soon."')


def defy(world: World, tenant: Entity, tool: Tool) -> None:
    tenant.memes["defiance"] += 1
    world.say(
        f'But {tenant.id} shook {tenant.pronoun("possessive")} head and said, '
        f'"I will only tap it once, and then I will see."'
    )


def do_wrong(world: World, tool: Tool, blossom: Blossom) -> None:
    _do_wrong(world, world.get("tool"))
    world.say(
        f"{tool.label.capitalize()} flashed in the light; the bud was touched too hard. "
        f"The {blossom.label} trembled, and the {blossom.label_word} took a bruise."
    )


def alarm(world: World, keeper: Entity, tenant: Entity, blossom: Blossom) -> None:
    world.say(
        f'"Oh no!" cried {keeper.id}. "When rough hands race, the little green {blossom.label_word} may not bloom for days."'
    )


def rescue(world: World, keeper: Entity, response: Response, blossom: Blossom, delay: int) -> None:
    if contained(response, delay):
        world.get("ovary").meters["hurt"] = 0.0
        world.say(
            f"{keeper.id} came at once and {response.text.replace('{blossom}', blossom.label)}."
        )
        world.say(
            f"The bruised place settled down, the room grew still, and the blossom kept its chance to turn to fruit."
        )
    else:
        world.get("ovary").meters["hurt"] += 1
        world.get("ovary").meters["bruise"] += 1
        world.say(
            f"{keeper.id} came at once and {response.fail.replace('{blossom}', blossom.label)}."
        )
        world.say(
            f"The bruise spread, and the shy bloom lost its little race."
        )


def moral(world: World, keeper: Entity, tenant: Entity, blossom: Blossom) -> None:
    tenant.memes["lesson"] += 1
    tenant.memes["relief"] += 1
    keeper.memes["relief"] += 1
    world.say("For a breath, the room was quiet as a held note.")
    world.say(
        f"Then {keeper.id} smiled, not scolding but teaching: \"A small thing that grows deserves a soft hand. "
        f"Rough taps make trouble; gentle care makes fruit.\""
    )
    world.say(
        f"{tenant.id} nodded. \"Soft hands save the day,\" {tenant.id} said. \"Hard hands spoil the fray.\""
    )


def ending(world: World, keeper: Entity, tenant: Entity, setting: Setting, blossom: Blossom) -> None:
    tenant.memes["joy"] += 1
    world.say(
        f"The next morning, {keeper.id} set a bowl of honeyed pears on the table, "
        f"and the same {blossom.label} had opened wide, bright as a lantern."
    )
    world.say(
        f"{tenant.id} dusted {tenant.pronoun('possessive')} hands, smiled at the window, "
        f"and helped water the pot instead. In that calm little room, good care won the day."
    )


def tell(setting: Setting, tool: Tool, blossom: Blossom, response: Response,
         tenant_name: str = "Robin", tenant_gender: str = "boy",
         keeper_name: str = "Moss", keeper_gender: str = "girl",
         delay: int = 0) -> World:
    world = World(setting)
    tenant = world.add(Entity(id=tenant_name, kind="character", type=tenant_gender, role="tenant"))
    keeper = world.add(Entity(id=keeper_name, kind="character", type=keeper_gender, role="keeper"))
    ovary = world.add(Entity(id="ovary", type="thing", label="ovary"))
    tool_ent = world.add(Entity(id="tool", type="thing", label=tool.label))
    world.facts["tenant"] = tenant
    world.facts["keeper"] = keeper
    world.facts["tool"] = tool_ent
    world.facts["blossom"] = blossom
    world.facts["response"] = response
    world.facts["delay"] = delay

    opening(world, tenant, keeper, setting, blossom)
    world.para()
    want_shiny(world, tenant, tool)
    warn(world, keeper, tenant, blossom)
    defy(world, tenant, tool)
    world.para()
    do_wrong(world, tool, blossom)
    alarm(world, keeper, tenant, blossom)
    rescue(world, keeper, response, blossom, delay)
    moral(world, keeper, tenant, blossom)
    world.para()
    ending(world, keeper, tenant, setting, blossom)

    outcome = "contained" if contained(response, delay) else "damaged"
    world.facts["outcome"] = outcome
    world.facts["hurt"] = world.get("ovary").meters["hurt"] >= THRESHOLD
    return world


SETTINGS = {
    "orchard": Setting("orchard", "the orchard", "spring", "soft"),
    "greenhouse": Setting("greenhouse", "the greenhouse", "spring", "warm"),
    "garden": Setting("garden", "the garden", "summer", "gentle"),
}

TOOLS = {
    "pin": Tool("pin", "a silver pin", sharp=True),
    "thorn": Tool("thorn", "a rose thorn", sharp=True),
}

BLOSSOMS = {
    "pear": Blossom("pear", "pear blossom", "the pear blossom", "the stem"),
    "apple": Blossom("apple", "apple blossom", "the apple blossom", "the branch"),
    "plum": Blossom("plum", "plum blossom", "the plum blossom", "the twig"),
}

RESPONSES = {
    "cup_hands": Response("cup_hands", 3, 2,
                          "cupped the blossom with both hands and lifted it from the wind",
                          "tried to cup the blossom, but the bruise had already spread",
                          "cupped the blossom with both hands and kept it safe"),
    "wrap_cloth": Response("wrap_cloth", 3, 3,
                           "wrapped a soft cloth around the stem and steadied it on the table",
                           "wrapped a cloth around it, but the bruise had already spread",
                           "wrapped a soft cloth around the stem and steadied it"),
    "call_help": Response("call_help", 2, 1,
                          "called for help and covered the bloom with a bowl",
                          "called for help, but the bruise had already spread",
                          "called for help and covered the bloom with a bowl"),
    "flick_water": Response("flick_water", 1, 1,
                            "flicked a little water at the bruise",
                            "flicked water at it, but that did no good",
                            "flicked a little water at the bruise"),
}

SENSE_MIN = 2

NAMES_B = ["Robin", "Pip", "Wren", "Milo", "Toby", "Theo"]
NAMES_G = ["Moss", "Lila", "Nina", "Daisy", "Ivy", "Mira"]

CURATED = [
    StoryParams("orchard", "pin", "pear", "Robin", "boy", "Moss", "girl", 0),
    StoryParams("greenhouse", "thorn", "apple", "Mira", "girl", "Theo", "boy", 1),
    StoryParams("garden", "pin", "plum", "Pip", "boy", "Lila", "girl", 0),
]


@dataclass
class StoryParams:
    setting: str
    tool: str
    blossom: str
    tenant_name: str
    tenant_gender: str
    keeper_name: str
    keeper_gender: str
    delay: int = 0
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, t, b) for s in SETTINGS for t in TOOLS for b in BLOSSOMS if reasonableness_gate(TOOLS[t], BLOSSOMS[b])]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a tenant, an ovary, a fable, and a moral.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--blossom", choices=BLOSSOMS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
    if args.tool and args.blossom and not reasonableness_gate(TOOLS[args.tool], BLOSSOMS[args.blossom]):
        raise StoryError("No story: the tool is sharp, but the blossom is not delicate enough for this fable.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.tool is None or c[1] == args.tool)
              and (args.blossom is None or c[2] == args.blossom)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, tool, blossom = rng.choice(sorted(combos))
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    tenant_gender = rng.choice(["boy", "girl"])
    keeper_gender = "girl" if tenant_gender == "boy" else "boy"
    tenant_name = rng.choice(NAMES_B if tenant_gender == "boy" else NAMES_G)
    keeper_name = rng.choice(NAMES_G if keeper_gender == "girl" else NAMES_B)
    return StoryParams(setting, tool, blossom, tenant_name, tenant_gender, keeper_name, keeper_gender, delay)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    tenant, keeper, blossom = f["tenant"], f["keeper"], f["blossom"]
    return [
        f'Write a fable for a small child that includes the words "tenant" and "ovary".',
        f"Tell a gentle rhyme about {tenant.id}, a tenant in {world.setting.place}, who almost hurts the {blossom.label_word} but learns a moral from {keeper.id}.",
        f"Write a short moral story where rough hands are replaced by careful hands, and the ending feels bright and safe.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tenant, keeper, blossom = f["tenant"], f["keeper"], f["blossom"]
    out = [
        ("Who is the story about?",
         f"It is about {tenant.id}, a tenant in {world.setting.place}, and {keeper.id}, who helped with the garden care."),
        ("What did the tenant want to do?",
         f"{tenant.id} wanted to use a sharp tool on the bloom because the shiny idea seemed clever at first."),
        ("What did the helper warn about?",
         f"{keeper.id} warned that the {blossom.label} holds an ovary inside it, so rough pokes can bruise the growing part."),
    ]
    if f["hurt"]:
        out.append((
            "What happened when the tenant used the tool?",
            f"The ovary was hurt and bruised. The harm happened because the sharp tap was too rough for something so delicate."
        ))
    if f["outcome"] == "contained":
        out.append((
            "How did the helper fix the problem?",
            f"{keeper.id} used {f['response'].qa_text} so the blossom could settle and keep growing. That gentle action kept the story from becoming sad."
        ))
        out.append((
            "What moral did they learn?",
            "Gentle hands make good things grow, but rough hands can spoil them. The lesson is to treat small growing things with care."
        ))
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a tenant?",
         "A tenant is someone who lives in a place that belongs to someone else and pays or agrees to stay there."),
        ("What is an ovary in a flower?",
         "A flower's ovary is the part that can hold seeds and later help make fruit."),
        ("Why should delicate blossoms be handled gently?",
         "Delicate blossoms can bruise easily, and bruises can keep them from growing well."),
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], TOOLS[params.tool], BLOSSOMS[params.blossom],
                 RESPONSES["cup_hands"], params.tenant_name, params.tenant_gender,
                 params.keeper_name, params.keeper_gender, params.delay)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


ASP_RULES = r"""
delicate(b) :- blossom(b).
valid(s,t,b) :- setting(s), tool(t), blossom(b), sharp(t), delicate(b).
outcome(contained) :- response(r), power(r,P), delay(D), P >= D + 1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for t, obj in TOOLS.items():
        lines.append(asp.fact("tool", t))
        if obj.sharp:
            lines.append(asp.fact("sharp", t))
    for b in BLOSSOMS:
        lines.append(asp.fact("blossom", b))
    for r in RESPONSES.values():
        lines.append(asp.fact("response", r.id))
        lines.append(asp.fact("power", r.id, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between clingo and Python valid_combos()")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: smoke test generate() succeeded.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


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
    StoryParams("orchard", "pin", "pear", "Robin", "boy", "Moss", "girl", 0),
    StoryParams("greenhouse", "thorn", "apple", "Mira", "girl", "Theo", "boy", 1),
    StoryParams("garden", "pin", "plum", "Pip", "boy", "Lila", "girl", 0),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(map(str, asp_valid_combos())))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
