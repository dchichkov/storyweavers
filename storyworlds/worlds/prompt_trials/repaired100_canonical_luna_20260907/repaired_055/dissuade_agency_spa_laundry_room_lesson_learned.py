#!/usr/bin/env python3
"""
A standalone storyworld about a laundry-room spa, a risky idea, and the
kindness of learning from a mistake.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}


@dataclass
class Setting:
    place: str = "the laundry room"
    areas: list[str] = field(
        default_factory=lambda: [
            "the folding table",
            "the humming washers",
            "the little ironing corner",
        ]
    )


@dataclass(frozen=True)
class Mishap:
    id: str
    object_name: str
    risky_plan: str
    warning: str
    consequence: str
    clue: str
    dissuasion: str
    repair: str
    lesson: str
    ending: str
    spa_detail: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {"laundry": Setting()}

GIRL_NAMES = ["Luna", "Maya", "Nora", "Pia", "Tess", "Ivy"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Finn", "Ezra", "Noah"]
TRAITS = ["inventive", "cheerful", "curious", "bold", "quick-thinking", "playful"]

MISHAPS = [
    Mishap(
        id="soap_bubbles",
        object_name="a basket of clean towels",
        risky_plan="turn the folding table into a luxury spa by pouring bubble soap over every towel",
        warning="the bottle label showed a tiny crossed-out towel",
        consequence="a foamy river slid across the floor and made the towels wobble like sleepy boats",
        clue="the label also showed a single drop beside a washing machine, not beside the towels",
        dissuasion="Please do not use all the soap. A spa can use one small scoop, and towels need to stay dry until their turn.",
        repair="mopped the foamy floor, rinsed the table, and folded the towels again",
        lesson="being imaginative is wonderful, but agency means choosing carefully when an idea could affect other people",
        ending="one neat towel wore a tiny bubble crown while the clean floor shone around it",
        spa_detail="a warm-scented hand towel and a paper cup of pretend cucumber water",
    ),
    Mishap(
        id="dryer_salon",
        object_name="a pile of wool socks",
        risky_plan="make a dryer salon by placing loose socks on the hot dryer and spraying them with water",
        warning="the dryer sign said to keep loose things away from its vent",
        consequence="the socks puffed into lumpy clouds while the dryer began thumping like a drum",
        clue="a cool-air symbol pointed to the empty basket beside the dryer",
        dissuasion="Let us use the basket for the spa. The dryer needs clear air, and wet socks do not belong on top.",
        repair="stopped the dryer, moved the socks into the basket, and checked that nothing blocked the vent",
        lesson="a funny plan can still be changed when someone gives a clear warning",
        ending="the socks rested in a basket like a row of woolly spa guests",
        spa_detail="soft socks rolled into cushions for an imaginary foot-care salon",
    ),
    Mishap(
        id="iron_mirror",
        object_name="a shiny ironing board",
        risky_plan="make an agency mirror by balancing the hot iron upright so everyone could admire their hair",
        warning="the iron's red heat light blinked beside a picture of a lowered iron",
        consequence="the board trembled and the iron skated toward a lace cloth",
        clue="the heat light changed from red only after the iron was placed safely on its heel",
        dissuasion="I know the mirror idea is funny, but the hot iron must stay still. We can make a paper mirror instead.",
        repair="unplugged the iron, moved the lace away, and drew a bright paper mirror",
        lesson="agency is not doing every idea immediately; it is making a safe choice and helping repair trouble",
        ending="the paper mirror showed two silly faces without a single scorch mark",
        spa_detail="paper crowns, pretend robes, and a peppermint-scented drawing",
    ),
    Mishap(
        id="scented_rinse",
        object_name="a row of clean shirts",
        risky_plan="open every scent bottle to give the laundry room a fancy spa smell",
        warning="each bottle had a closed-lid picture and a warning about mixing scents",
        consequence="lemon, lavender, and pine chased one another through the air until everyone sneezed",
        clue="the scent chart showed one tiny dot for a single approved drop",
        dissuasion="One scent is enough. Please close the bottles before our noses start a parade.",
        repair="closed the bottles, opened a window, and made one gentle scent card instead",
        lesson="a small choice can be more thoughtful than a giant one, especially when a shared room is involved",
        ending="the shirts smelled faintly of lavender while the sneeze parade marched away",
        spa_detail="a lavender scent card tucked beside the folded shirts",
    ),
    Mishap(
        id="laundry_cafe",
        object_name="a rolling cart of folded blankets",
        risky_plan="serve a laundry-room spa breakfast by putting juice cups on the moving cart",
        warning="the cart's wheels were marked with a red line and a picture of steady hands",
        consequence="the cart rolled, the cups wobbled, and one orange splash landed on a blanket",
        clue="the nearby shelf held a stable tray with a handle",
        dissuasion="The cart is for carrying blankets. Let us use the steady tray for pretend drinks.",
        repair="blotted the blanket, parked the cart, and carried the pretend drinks on the tray",
        lesson="reconciliation begins when people admit what went wrong and choose a better tool together",
        ending="the blanket dried beside a tray of pretend orange tea, safe from rolling wheels",
        spa_detail="pretend orange tea served on a steady tray",
    ),
    Mishap(
        id="sock_massage",
        object_name="a mountain of unmatched socks",
        risky_plan="give every sock a massage by stuffing it into the spinning washer",
        warning="the washer door displayed a picture of clothes only, never loose objects",
        consequence="the unmatched socks tumbled into a wild whirlpool and one tiny sock vanished",
        clue="a matching basket stood beside the washer with a picture of pairs",
        dissuasion="The washer is for washing clothes, not sorting them. Let us pair the socks in the basket instead.",
        repair="stopped the machine, found the tiny sock, and matched the pairs by color",
        lesson="a helper can dissuade a risky plan without taking away someone's agency",
        ending="the matched socks sat in pairs like guests waiting for a very quiet spa",
        spa_detail="a sorting spa where every sock received a matching partner",
    ),
]

MODES = ["suspense", "dialogue", "comic", "object", "question", "reconciliation"]


@dataclass
class StoryParams:
    place: str = "laundry"
    activity: str = "spa"
    name: str = "Luna"
    gender: str = "girl"
    friend_name: str = "Owen"
    friend_gender: str = "boy"
    trait: str = "inventive"
    seed: Optional[int] = None


def reasonable(params: StoryParams) -> bool:
    return (
        params.place == "laundry"
        and params.activity == "spa"
        and params.gender in {"girl", "boy"}
        and params.friend_gender in {"girl", "boy"}
        and params.name != params.friend_name
    )


def valid_names(gender: str) -> list[str]:
    return GIRL_NAMES if gender == "girl" else BOY_NAMES


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A comic laundry-room spa storyworld about agency and a lesson learned."
    )
    parser.add_argument("--place", choices=SETTINGS.keys())
    parser.add_argument("--activity", choices=["spa"])
    parser.add_argument("--gender", choices=["girl", "boy"])
    parser.add_argument("--friend-gender", dest="friend_gender", choices=["girl", "boy"])
    parser.add_argument("--name")
    parser.add_argument("--friend-name", dest="friend_name")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or "laundry"
    activity = args.activity or "spa"
    if place != "laundry":
        raise StoryError("This storyworld is set in the laundry room.")
    if activity != "spa":
        raise StoryError("This storyworld's activity is the pretend laundry-room spa.")
    gender = args.gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if gender == "girl" else "girl")
    name = args.name or rng.choice(valid_names(gender))
    friend_name = args.friend_name or rng.choice(valid_names(friend_gender))
    if name == friend_name:
        raise StoryError("The two children must have different names.")
    return StoryParams(
        place=place,
        activity=activity,
        name=name,
        gender=gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        trait=rng.choice(TRAITS),
    )


def add_meter(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] = entity.meters.get(key, 0.0) + amount


def add_meme(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + amount


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    child = world.add(Entity(params.name, "character", params.gender))
    friend = world.add(Entity(params.friend_name, "character", params.friend_gender))
    washer = world.add(Entity("washer", "thing", "washer", "large washing machine"))
    spa = world.add(Entity("spa", "thing", "spa", "pretend laundry-room spa"))

    route = params.seed if params.seed is not None else sum(
        ord(c) for c in params.name + params.friend_name
    )
    mishap = MISHAPS[route % len(MISHAPS)]
    mode = MODES[(route // len(MISHAPS)) % len(MODES)]

    if mode == "suspense":
        world.say(
            f"The laundry room hummed while {params.name} carried {mishap.object_name} "
            f"toward a pretend spa."
        )
        world.say(
            f"{params.name} had a {params.trait} plan: to {mishap.risky_plan}."
        )
    elif mode == "dialogue":
        world.say(
            f'"Welcome to our spa!" {params.name} announced as {params.friend_name} '
            f"sorted clothes in the laundry room."
        )
        world.say(f'"I hope the spa has a safe plan," {params.friend_name} said.')
    elif mode == "comic":
        world.say(
            f"{params.name} wore a towel like a cape, and {params.friend_name} wore "
            "two clothespins like royal earrings."
        )
        world.say(
            f"They were opening a laundry-room spa, though {params.name}'s first idea "
            f"was to {mishap.risky_plan}."
        )
    elif mode == "object":
        world.say(
            f"{mishap.object_name.capitalize()} sat beneath the bright lights of the "
            "laundry room."
        )
        world.say(
            f"{params.name}, an {params.trait} child, saw a chance to make a spa "
            f"and decided to {mishap.risky_plan}."
        )
    elif mode == "question":
        world.say(
            f'"Can a laundry room become a spa?" {params.name} asked while the washers '
            "bubbled and thumped."
        )
        world.say(
            f"{params.friend_name} smiled, but {params.name} already wanted to "
            f"{mishap.risky_plan}."
        )
    else:
        world.say(
            f"{params.name} and {params.friend_name} had promised to make a funny "
            "laundry-room spa together."
        )
        world.say(
            f"Then {params.name} announced a plan to {mishap.risky_plan}, and the "
            "promise suddenly felt wobbly."
        )

    world.say(f"The plan sounded exciting. It also made the laundry room go very quiet.")
    world.para()
    add_meme(child, "excitement", 1)
    add_meme(child, "overconfidence", 1)
    add_meter(child, "agency", 1)
    world.say(f"{params.name} began. For one suspenseful moment, everything seemed fine.")
    world.say(f"Then {mishap.consequence}.")
    world.say(f"{params.friend_name} saw that {mishap.warning}.")
    add_meme(friend, "worry", 1)
    add_meter(friend, "attention", 1)

    world.para()
    world.say(f"{params.friend_name} took a breath and said, \"{mishap.dissuasion}\"")
    world.say(
        f"{params.name} frowned. \"Are you telling me what to do?\" "
        f"{params.friend_name} shook their head and replied, "
        "\"No. I am giving you the choice to pause, listen, and decide safely.\""
    )
    world.say(f"That made {params.name} look again. {mishap.clue}.")
    add_meme(friend, "kindness", 1)
    add_meme(child, "understanding", 1)
    add_meter(child, "agency", 1)
    world.say(
        f"{params.name} nodded. \"I choose to stop. I wanted a funny spa, not a "
        "laundry-room disaster.\""
    )

    world.para()
    world.say(f"Together, the children {mishap.repair}.")
    world.say(
        f"{params.name} apologized. \"I was so eager to make the spa special that I "
        "forgot this room belongs to everyone.\""
    )
    world.say(
        f"{params.friend_name} smiled. \"And I sounded bossy when I was worried. "
        "Can we start again?\""
    )
    world.say(
        f'"Yes," said {params.name}. "You can help me think, and I can make the final '
        "safe choice.\""
    )
    add_meme(child, "relief", 1)
    add_meme(child, "friendship", 1)
    add_meme(friend, "relief", 1)
    add_meme(friend, "friendship", 1)
    add_meter(child, "care", 1)
    add_meter(friend, "care", 1)

    world.para()
    world.say(
        f"They rebuilt the spa with {mishap.spa_detail}. The washers hummed like "
        "tiny applause."
    )
    world.say(f"{params.name} said, \"A lesson learned can be part of the spa too.\"")
    world.say(f"{params.friend_name} answered, \"Especially if it comes with clean towels.\"")
    world.say(
        f"They learned that {mishap.lesson}. Their reconciliation felt warmer than "
        "any dryer."
    )
    world.say(f"At last, {mishap.ending}.")

    world.facts.update(
        child=child,
        friend=friend,
        washer=washer,
        spa=spa,
        mishap=mishap,
        mode=mode,
        resolved=True,
        dissuaded=True,
        agency=True,
        reconciliation=True,
        lesson_learned=True,
        suspense=True,
        comedy=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    mishap = world.facts["mishap"]
    child = world.facts["child"]
    friend = world.facts["friend"]
    return [
        "Write a child-friendly comedy set in a laundry room where a pretend spa creates suspense.",
        f"Show {child.id} making a risky spa plan, while {friend.id} dissuades the plan without taking away {child.id}'s agency.",
        f"Include reconciliation, a lesson learned, and this concrete ending image: {mishap.ending}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    friend = world.facts["friend"]
    mishap = world.facts["mishap"]
    return [
        QAItem(
            question=f"What risky plan did {child.id} make?",
            answer=f"{child.id} planned to {mishap.risky_plan}. The idea sounded funny, but it could affect the shared laundry room.",
        ),
        QAItem(
            question=f"How did {friend.id} dissuade {child.id}?",
            answer=f"{friend.id} pointed out that {mishap.warning} and said, \"{mishap.dissuasion}\" The friend offered a safe choice instead of taking away {child.id}'s agency.",
        ),
        QAItem(
            question="What helped the children understand that the plan was unsafe?",
            answer=f"They looked again and noticed that {mishap.clue}. That concrete clue helped them pause and change the plan.",
        ),
        QAItem(
            question="How did the children reconcile?",
            answer=f"{child.id} apologized for rushing, and {friend.id} apologized for sounding bossy. Then they {mishap.repair} together.",
        ),
        QAItem(
            question="What lesson did they learn?",
            answer=f"They learned that {mishap.lesson}.",
        ),
        QAItem(
            question="What final image showed that the laundry-room spa was safe?",
            answer=f"At the end, {mishap.ending}. The image showed that the children had repaired the trouble.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a spa?",
            answer="A spa is a place or activity associated with relaxation and gentle care, such as resting, washing, or enjoying a pleasant scent.",
        ),
        QAItem(
            question="What does agency mean?",
            answer="Agency means having the ability to make choices and take responsible action.",
        ),
        QAItem(
            question="Why is it useful to dissuade someone kindly?",
            answer="Kind dissuasion can help someone pause and notice a danger while still respecting that person's ability to choose.",
        ),
        QAItem(
            question="Why should people be careful in a laundry room?",
            answer="Laundry rooms contain water, electricity, heat, moving machines, and slippery floors, so people should follow instructions and ask an adult for help when needed.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
child(C) :- child_name(C).
friend(F) :- friend_name(F).
setting(laundry).
activity(spa).
risky_plan(C) :- child(C), planned_spa(C).
dissuaded(F,C) :- friend(F), child(C), warning(F,C).
agency(C) :- child(C), chose_pause(C).
reconciliation(C,F) :- child(C), friend(F), apologized(C), apologized(F).
lesson_learned(C) :- agency(C), dissuaded(_,C), reconciliation(C,_).
resolved(C) :- lesson_learned(C).
#show resolved/1.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("child_name", "child"),
            asp.fact("friend_name", "friend"),
            asp.fact("setting", "laundry"),
            asp.fact("activity", "spa"),
            asp.fact("planned_spa", "child"),
            asp.fact("warning", "friend", "child"),
            asp.fact("chose_pause", "child"),
            asp.fact("apologized", "child"),
            asp.fact("apologized", "friend"),
        ]
    )


def asp_program(show: str = "#show resolved/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    atoms = asp.atoms(model, "resolved")
    if atoms == [("child",)]:
        print("OK: ASP and Python reasonableness agree.")
        return 0
    print("MISMATCH between ASP and Python reasonableness.")
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        details = []
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(
            f"  {entity.id:10} ({entity.type:10}) {' '.join(details)}".rstrip()
        )
    lines.append(f"  facts      {sorted(k for k, v in world.facts.items() if v is True)}")
    return "\n".join(lines)


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def valid_story_params() -> list[StoryParams]:
    return [
        StoryParams(
            place="laundry",
            activity="spa",
            name="Luna",
            gender="girl",
            friend_name="Owen",
            friend_gender="boy",
            trait="inventive",
        ),
        StoryParams(
            place="laundry",
            activity="spa",
            name="Milo",
            gender="boy",
            friend_name="Nora",
            friend_gender="girl",
            trait="cheerful",
        ),
        StoryParams(
            place="laundry",
            activity="spa",
            name="Pia",
            gender="girl",
            friend_name="Theo",
            friend_gender="boy",
            trait="curious",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    if not reasonable(params):
        raise StoryError(
            "This world requires a laundry-room spa story with two different child names."
        )
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        result = asp_verify()
        if result:
            sys.exit(result)
        for params in valid_story_params():
            sample = generate(params)
            if not sample.story or len(sample.story_qa) < 3:
                print("MISMATCH: generated story verification failed.")
                sys.exit(1)
        print("OK: generated stories passed.")
        return

    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print("resolved:", asp.atoms(model, "resolved"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in valid_story_params()]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            seed = base_seed + index
            index += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as error:
                print(error)
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.name} and {sample.params.friend_name} in the laundry room"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
