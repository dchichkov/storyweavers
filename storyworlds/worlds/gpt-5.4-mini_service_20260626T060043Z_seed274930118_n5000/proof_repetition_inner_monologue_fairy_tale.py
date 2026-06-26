#!/usr/bin/env python3
"""
A tiny fairy-tale storyworld about proof, repetition, and inner monologue.

Seed tale:
A little lantern-keeper named Elin wants to enter a moon gate, but the gatekeeper
asks for proof. Elin must repeat a brave little rhyme, listen to her own thoughts,
and bring back the right proof from a magical place. In the end, the gate opens
because the proof is real, and so is Elin's courage.

This world generates short, complete fairy-tale stories with:
- a concrete setting
- a question that creates tension
- repeated attempts or repeated phrases
- an inner-monologue beat
- a resolution that shows what changed
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "princess", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "prince", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    want: str
    repeated_want: str
    action: str
    trial: str
    inner_voice: str
    success_image: str
    proof_kind: str
    keywords: set[str] = field(default_factory=set)


@dataclass
class Proof:
    id: str
    label: str
    phrase: str
    kind: str
    grants: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    quest: str
    proof: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "moon_gate": Setting("the moon gate", "silver-bright", {"listen", "speak", "wait"}),
    "forest_path": Setting("the forest path", "quiet", {"seek", "listen", "speak"}),
    "rose_garden": Setting("the rose garden", "sweet", {"seek", "listen", "speak"}),
    "river_stone": Setting("the river stone", "hushed", {"seek", "listen", "speak"}),
}

QUESTS = {
    "open_gate": Quest(
        id="open_gate",
        want="open the moon gate",
        repeated_want="open the moon gate",
        action="knock on the silver door",
        trial="the gatekeeper would not open the gate without proof",
        inner_voice="I can be brave, she told herself. I can be brave.",
        success_image="the moon gate swung open like a quiet smile",
        proof_kind="moonproof",
        keywords={"proof", "gate", "moon"},
    ),
    "save_lily": Quest(
        id="save_lily",
        want="help the sleeping lily bloom",
        repeated_want="help the sleeping lily bloom",
        action="speak the waking rhyme",
        trial="the lily would not wake unless the right proof was found",
        inner_voice="If I speak gently and try again, the flower may hear me.",
        success_image="the lily opened its white petals at last",
        proof_kind="dewproof",
        keywords={"proof", "flower", "dew"},
    ),
    "find_song": Quest(
        id="find_song",
        want="find the lost song",
        repeated_want="find the lost song",
        action="call into the hollow tree",
        trial="the song stayed hidden until the right proof was brought back",
        inner_voice="I heard it once. I can hear it again.",
        success_image="the hidden melody came fluttering home",
        proof_kind="songproof",
        keywords={"proof", "song", "tree"},
    ),
}

PROOFS = {
    "moon_silver": Proof(
        id="moon_silver",
        label="a silver moon-feather",
        phrase="a silver moon-feather",
        kind="moonproof",
        grants={"open_gate"},
    ),
    "dew_pearl": Proof(
        id="dew_pearl",
        label="a pearl of dew",
        phrase="a pearl of dew",
        kind="dewproof",
        grants={"save_lily"},
    ),
    "song_bell": Proof(
        id="song_bell",
        label="a little bell with a clear note",
        phrase="a little bell with a clear note",
        kind="songproof",
        grants={"find_song"},
    ),
}

HELPERS = {
    "owl": ("an old owl", "wise"),
    "mouse": ("a shy mouse", "small"),
    "deer": ("a soft deer", "gentle"),
}

GIRL_NAMES = ["Elin", "Mira", "Nora", "Luna", "Tilda", "Ivy"]
BOY_NAMES = ["Arin", "Theo", "Finn", "Eli", "Rowan", "Noel"]
TRAITS = ["brave", "curious", "gentle", "patient", "hopeful"]


def reasonableness_gate(quest: Quest, proof: Proof) -> bool:
    return quest.id in proof.grants and quest.proof_kind == proof.kind


def explain_rejection(quest: Quest, proof: Proof) -> str:
    return (
        f"(No story: {proof.label} is not the right proof for {quest.want}. "
        f"The proof must match the trial, so this combination is rejected.)"
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for quest_id, quest in QUESTS.items():
            if "seek" not in setting.affords and quest_id != "open_gate":
                pass
            for proof_id, proof in PROOFS.items():
                if reasonableness_gate(quest, proof):
                    combos.append((place, quest_id, proof_id))
    return combos


def _do_repetition(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["doubt"] = hero.memes.get("doubt", 0.0) + 0.5
    hero.memes["steadiness"] = hero.memes.get("steadiness", 0.0) + 1.0
    world.say(
        f"{hero.id} whispered the same little wish three times: "
        f'"{quest.repeated_want}." "{quest.repeated_want}." "{quest.repeated_want}."'
    )
    world.say(f"Each time, the wish sounded steadier, as if the words were making a path.")


def _inner_monologue(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["courage"] = hero.memes.get("courage", 0.0) + 1.0
    world.say(f"In {hero.pronoun('possessive')} heart, {quest.inner_voice}")


def _find_proof(world: World, hero: Entity, proof: Proof) -> None:
    proof_ent = world.add(Entity(
        id=proof.id,
        type="proof",
        label=proof.label,
        phrase=proof.phrase,
        owner=hero.id,
    ))
    proof_ent.worn_by = hero.id
    hero.meters["proof"] = hero.meters.get("proof", 0.0) + 1.0
    world.say(f"At last, {hero.id} found {proof.phrase} and held it close.")


def tell(setting: Setting, quest: Quest, proof: Proof, hero_name: str, hero_gender: str,
         helper_kind: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        traits=["little", trait],
        meters={"proof": 0.0},
        memes={"doubt": 0.0, "courage": 0.0, "steadiness": 0.0, "hope": 0.0},
    ))
    helper_label, helper_trait = HELPERS[helper_kind]
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_kind,
        label=helper_label,
        traits=[helper_trait],
    ))
    gatekeeper = world.add(Entity(
        id="gatekeeper",
        kind="character",
        type="owl",
        label="the gatekeeper",
        traits=["old", "careful"],
    ))

    world.say(
        f"Once upon a time, there was a little {trait} {hero_gender} named {hero.id} "
        f"who lived near {setting.place}."
    )
    world.say(
        f"{hero.id} wanted to {quest.want}, but {gatekeeper.label} said, "
        f'"Not yet. Bring me proof."'
    )

    world.para()
    world.say(
        f"{helper.label.capitalize()} came beside {hero.id}, and together they went "
        f"through {setting.place}."
    )
    _do_repetition(world, hero, quest)
    _inner_monologue(world, hero, quest)
    world.say(f"{helper.label.capitalize()} pointed kindly toward the hidden places where proof might wait.")

    world.para()
    world.say(f"They searched under leaves, over stones, and beside the quiet water.")
    _find_proof(world, hero, proof)
    world.say(f"{gatekeeper.label.capitalize()} examined it carefully and nodded once.")
    world.say(f'"That is proof enough," said {gatekeeper.label}.')

    world.para()
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1.0
    world.say(
        f"So {hero.id} took a breath and {quest.action}. "
        f"Then {quest.success_image}."
    )
    world.say(
        f"{helper.label.capitalize()} smiled, and {hero.id} felt the doubt grow small and small."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        gatekeeper=gatekeeper,
        quest=quest,
        proof=proof,
        setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fairy tale for a child about "{f["quest"].want}" and proof.',
        f"Tell a gentle story where {f['hero'].id} must find proof before the gatekeeper will listen.",
        f"Write a story with repetition and an inner monologue where a little hero learns that proof matters.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    proof = f["proof"]
    gatekeeper = f["gatekeeper"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at first?",
            answer=f"{hero.id} wanted to {quest.want}."
        ),
        QAItem(
            question=f"Why would {gatekeeper.label} not open the gate right away?",
            answer=f"Because {gatekeeper.label} wanted proof before opening the gate."
        ),
        QAItem(
            question=f"What proof did {hero.id} find?",
            answer=f"{hero.id} found {proof.phrase}."
        ),
        QAItem(
            question=f"Who helped {hero.id} search?",
            answer=f"{helper.label.capitalize()} helped {hero.id} search for proof."
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"At the end, the proof was accepted and {quest.success_image}."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    q = f["quest"]
    p = f["proof"]
    return [
        QAItem(
            question="What is proof?",
            answer="Proof is something that shows a thing is true or makes a reason believable."
        ),
        QAItem(
            question="Why do stories repeat a sentence sometimes?",
            answer="Stories repeat a sentence to make it feel important, magical, or memorable."
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet voice a character hears in their own mind."
        ),
        QAItem(
            question=f"Why was {p.label} the right proof for this story?",
            answer=f"Because it matched the kind of proof needed to {q.want}."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        out.append(f"{i}. {prompt}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        bits = []
        if ent.meters:
            bits.append(f"meters={ent.meters}")
        if ent.memes:
            bits.append(f"memes={ent.memes}")
        if ent.worn_by:
            bits.append(f"worn_by={ent.worn_by}")
        lines.append(f"  {ent.id:10} ({ent.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for q in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, q))
    for qid, quest in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("needs", qid, quest.proof_kind))
    for pr_id, proof in PROOFS.items():
        lines.append(asp.fact("proof", pr_id))
        lines.append(asp.fact("kind", pr_id, proof.kind))
        for g in sorted(proof.grants):
            lines.append(asp.fact("grants", pr_id, g))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(P,Q,R) :- quest(Q), proof(R), needs(Q,K), kind(R,K), grants(R,Q), place(P).
#show compatible/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about proof and repetition.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--quest", choices=QUESTS.keys())
    ap.add_argument("--proof", choices=PROOFS.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS.keys())
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.quest:
        combos = [c for c in combos if c[1] == args.quest]
    if args.proof:
        combos = [c for c in combos if c[2] == args.proof]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest_id, proof_id = rng.choice(sorted(combos))
    quest = QUESTS[quest_id]
    proof = PROOFS[proof_id]
    if args.gender is None:
        gender = rng.choice(["girl", "boy"])
    else:
        gender = args.gender
    if args.name is None:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    else:
        name = args.name
    helper = args.helper or rng.choice(list(HELPERS))
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest_id, proof=proof_id,
                       name=name, gender=gender, helper=helper, trait=trait)


CURATED = [
    StoryParams(place="moon_gate", quest="open_gate", proof="moon_silver", name="Elin", gender="girl", helper="owl", trait="brave"),
    StoryParams(place="forest_path", quest="find_song", proof="song_bell", name="Arin", gender="boy", helper="mouse", trait="curious"),
    StoryParams(place="rose_garden", quest="save_lily", proof="dew_pearl", name="Mira", gender="girl", helper="deer", trait="gentle"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], QUESTS[params.quest], PROOFS[params.proof],
                 params.name, params.gender, params.helper, params.trait)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combinations:")
        for c in combos:
            print(" ", c)
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
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.quest} with {p.proof}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
