#!/usr/bin/env python3
"""
A tiny mythic story world about a shishkebab, an ice spirit, and a fluid
offering that tests friendship and kindness.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    setting: str = "the cold valley"
    hero: str = "Ari"
    friend: str = "Mira"
    giver: str = "the river spirit"
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.name] = ent
        return ent

    def get(self, name: str) -> Entity:
        return self.entities[name]


SETTING_REGISTRY = {
    "the cold valley": {
        "tags": {"ice", "fluid", "myth"},
        "mood": "quiet and pale",
    },
    "the moonlit spring": {
        "tags": {"fluid", "myth"},
        "mood": "silver and still",
    },
    "the frozen grove": {
        "tags": {"ice", "myth"},
        "mood": "blue and secret",
    },
}


@dataclass(frozen=True)
class MythArc:
    title: str
    premise: str
    problem: str
    choice: str
    action: str
    result: str
    ending: str
    problem_answer: str
    choice_answer: str
    result_answer: str


MYTH_ARCS = [
    MythArc(
        title="The Bridge Beneath the Rime",
        premise="An ice bridge was said to wake only for travelers who carried a meal for someone else.",
        problem="A trapped ribbon of fluid knocked beneath the bridge, while a hungry fox cub waited on the wrong bank.",
        choice="{hero} wanted to warm the stones with the whole shishkebab, but {friend} broke off the best piece for the cub.",
        action="Together they laid the warm skewer in a crack and guided the freed meltwater toward the fox.",
        result="The bridge loosened without breaking, and the fox crossed beside them.",
        ending="three sets of footprints gleamed across the blue bridge beneath the first evening star",
        problem_answer="Meltwater was trapped under the ice bridge, and a hungry fox cub was stranded across it.",
        choice_answer="The friends gave the fox cub the best piece of their shishkebab instead of keeping all its warmth for themselves.",
        result_answer="Their shared meal and careful channel freed the meltwater, softened the bridge, and let the fox cross safely.",
    ),
    MythArc(
        title="The Orchard That Forgot Spring",
        premise="A frostbound orchard bore glassy fruit, although its roots had not tasted water for a hundred mornings.",
        problem="The spring's fluid had frozen into a clear bell, and striking it only made the trees shiver.",
        choice="When {giver} asked for payment, {hero} and {friend} offered their shishkebab to the orchard keeper, who had eaten nothing all day.",
        action="The keeper showed them how to hold the skewer like a sundial, turning its warm shadow slowly over the bell of ice.",
        result="The bell melted into singing channels, and every thirsty root received an equal stream.",
        ending="one red apple hung among the silver branches, warm in {friend}'s open palm",
        problem_answer="The orchard's spring had become a bell of ice, leaving the roots without water.",
        choice_answer="The friends fed the hungry orchard keeper before asking the spirit to help the trees.",
        result_answer="The keeper's sundial lesson helped them melt the bell gently and send water to every root.",
    ),
    MythArc(
        title="The Cup That Froze for Greed",
        premise="At the center of {setting} stood a cup whose sacred fluid froze whenever one person claimed it alone.",
        problem="{hero} lifted the cup first; ice raced over its rim and began climbing both friends' sleeves.",
        choice="{hero} set it down and said, \"My friend drinks before I do.\" {friend} answered by saving half the shishkebab for {hero}.",
        action="They held the cup together and passed it back and forth, taking one small sip and one small bite at a time.",
        result="Because neither tried to own the gift, the ice slipped away and the fluid stayed bright.",
        ending="the empty cup reflected two faces instead of one, and crumbs made a little ring around it",
        problem_answer="The sacred cup froze when one person tried to claim it, and its ice began trapping both friends.",
        choice_answer="Each friend put the other first: one offered the first drink, and the other saved half the shishkebab.",
        result_answer="Sharing every sip and bite broke the cup's greedy spell and released them from the ice.",
    ),
    MythArc(
        title="The White Serpent's Thirst",
        premise="People feared a white serpent that curled around the last unfrozen pool, but no one had asked why it guarded the fluid.",
        problem="The serpent's scales were stuck to the ice, and each frightened breath froze more of the pool.",
        choice="Instead of chasing it away, {friend} offered a fragrant piece of shishkebab while {hero} promised not to raise the skewer like a spear.",
        action="As the serpent ate, the friends wrapped its tail in their warm cloaks and poured trickles of pool water around each frozen scale.",
        result="Freed from pain, the serpent uncoiled and opened the pool to every creature in the valley.",
        ending="the serpent slept beside the water like a white ribbon, with its head resting near the harmless skewer",
        problem_answer="The white serpent guarded the pool because its scales were painfully frozen to the ice.",
        choice_answer="The friends treated the feared serpent kindly, feeding it and promising not to use the skewer as a weapon.",
        result_answer="Their patient warming freed the serpent, which then shared the pool with the whole valley.",
    ),
    MythArc(
        title="The Ferry of Stars",
        premise="A little ferry carried moonlight across a dark lake each night so lost travelers could find the shore.",
        problem="A sheet of ice pinned the ferry in place, and its jar of glowing fluid was fading before moonrise.",
        choice="{hero} offered to cross alone, but {friend} refused to leave the waiting travelers and divided the friends' shishkebab among them.",
        action="Fed and hopeful, everyone formed a line, rocking the ferry in rhythm while the friends traced warm circles with the empty skewer.",
        result="The ice cracked in a safe ring; the ferry floated free, and the jar caught the first beam of moonlight.",
        ending="a silver road stretched behind the ferry while every passenger held one another's hands",
        problem_answer="Ice trapped the moonlight ferry while its jar of glowing fluid was going dark.",
        choice_answer="The friends stayed with the stranded travelers and shared their shishkebab instead of escaping alone.",
        result_answer="The fed travelers worked together, freed the ferry, and restored its guiding light.",
    ),
    MythArc(
        title="The Well of Unkind Echoes",
        premise="An old well repeated every cruel word as ice, but returned each kind word as clear fluid.",
        problem="After two shepherds quarreled nearby, a tower of sharp echoes sealed the well's mouth.",
        choice="Though they were hungry, {hero} and {friend} invited the ashamed shepherds to share their shishkebab and begin again.",
        action="Between bites, each person named one good thing another had done; warm drops formed wherever the praise touched the ice.",
        result="The frozen echoes rounded into water and carried the apologies down to the thirsty fields.",
        ending="four cups stood on the mossy rim, and the well softly repeated the words \"Begin again\"",
        problem_answer="Cruel words had turned into sharp ice and sealed the echoing well.",
        choice_answer="The friends invited the quarreling shepherds to eat with them and speak kindly about one another.",
        result_answer="Their sincere praise melted the frozen echoes into water for the fields.",
    ),
    MythArc(
        title="The Snow Giant's Tear",
        premise="A lonely snow giant kept winter on the mountain, for he believed friendship belonged only to smaller folk.",
        problem="His single tear had frozen over the path, trapping a healing fluid inside a wall of ice.",
        choice="{friend} climbed close enough to offer the giant the first piece of shishkebab, and {hero} made room beside the fire.",
        action="While the giant told his story, the friends listened without laughing and caught the warming tear in their cooking bowl.",
        result="The wall melted from the inside, releasing the medicine and opening a path down the mountain.",
        ending="the giant's enormous skewer joined two little skewers above a fire that no wind could put out",
        problem_answer="The snow giant's frozen tear blocked the path and trapped healing fluid inside the ice.",
        choice_answer="The friends welcomed the lonely giant to their meal and listened respectfully to his story.",
        result_answer="The giant's warmer tear melted the wall, releasing the medicine and reopening the mountain path.",
    ),
    MythArc(
        title="The Fish Under the Mirror",
        premise="Silver fish carried dawn under a lake, stirring its fluid until the sun appeared.",
        problem="The lake froze too early one morning, leaving the smallest fish alone above the ice while its school swam below.",
        choice="{hero} was ready to hurry onward, but {friend} gave the shivering fish a mushroom from the shishkebab and asked everyone to wait.",
        action="Using the blunt skewer, they tapped the fish's swimming rhythm; below them, the school answered and found a thin place in the ice.",
        result="The fish broke through together, reunited their smallest member, and churned the lake until dawn rose.",
        ending="gold light spilled over the water as the little fish leaped once between the two friends",
        problem_answer="Early ice separated the smallest dawn fish from its school beneath the lake.",
        choice_answer="The friends stopped their journey, fed the shivering fish, and waited to help it find its school.",
        result_answer="Their rhythm guided the school to thin ice, where the fish reunited and stirred up the dawn.",
    ),
    MythArc(
        title="The Feast of the Two Winters",
        premise="Two winter spirits argued over which of them owned {setting}, freezing one side hard and flooding the other with restless fluid.",
        problem="Every new boast thickened the ice wall between them and drove another wave toward the village ovens.",
        choice="{hero} and {friend} would not choose a winner; they placed their shishkebab across the boundary and invited both spirits to supper.",
        action="One spirit cooled the fire when it flared, while the other poured water when it dimmed, and the friends thanked them equally.",
        result="Working in balance, the spirits shrank the wall and the flood until a gentle stream remained.",
        ending="steam curled from four shared plates while snow fell on one side of the table and flowers opened on the other",
        problem_answer="Competing winter spirits created both a growing ice wall and a flood that threatened the village.",
        choice_answer="The friends refused to take sides and invited both spirits to share one shishkebab supper.",
        result_answer="The spirits learned to balance cold and water, leaving only a gentle stream instead of a wall and flood.",
    ),
    MythArc(
        title="The Crown of Clear Ice",
        premise="A crown of ice promised command over every river, yet it could be lifted only by someone who did not want its power.",
        problem="{giver} set the crown above a spring, and its weight pressed all the fluid back underground.",
        choice="Both friends stepped away from the crown. They used their shishkebab to feed the families waiting with empty water jars.",
        action="Then {hero} and {friend} carried the heavy jars together, refusing the spirit's offer to make either one ruler.",
        result="The unwanted crown cracked into harmless hail, and the spring rose freely for everyone.",
        ending="children floated green leaves through a circle of melting jewels where the crown had been",
        problem_answer="The ice crown's weight forced the spring underground and left families with empty jars.",
        choice_answer="The friends rejected power, fed the waiting families, and chose to carry water together.",
        result_answer="Because nobody claimed the crown, it broke apart and the spring became free for everyone.",
    ),
    MythArc(
        title="The Lantern in the Avalanche",
        premise="A blue lantern held one drop of ancient fluid that could remember a safe road through any storm.",
        problem="An avalanche buried the lantern under ice just as distant bells warned that travelers were lost.",
        choice="{friend} gave the last warm pieces of shishkebab to an exhausted searcher, while {hero} trusted the searcher's faint memory of the slope.",
        action="The three probed gently with the bare skewer, listening after every touch until the lantern chimed below them.",
        result="Its awakened drop drew a blue path through the snow, and they led every lost traveler home.",
        ending="the lantern hung above a crowded doorway, shining on an empty platter and many safe faces",
        problem_answer="An avalanche buried the road-finding lantern while travelers were lost in the storm.",
        choice_answer="The friends fed and trusted an exhausted searcher instead of keeping their food or ignoring the searcher's memory.",
        result_answer="Together they found the lantern, whose ancient drop showed everyone a safe blue path home.",
    ),
    MythArc(
        title="The River That Would Not Choose",
        premise="A young river had reached three villages but possessed only enough fluid to flow toward one of them.",
        problem="Ice gates guarded the three channels, and each village begged {giver} to open its gate first.",
        choice="{hero} and {friend} split their shishkebab into three equal portions and asked each village to send helpers to the others.",
        action="The mixed teams warmed one gate at a time, then used the skewer to mark fair water levels along every channel.",
        result="Because kindness traveled before the river, all three gates opened and friendship kept the channels equally full.",
        ending="three streams met around a willow whose roots held the polished skewer like a tiny golden branch",
        problem_answer="The young river had too little water for three villages, whose channels were closed by ice gates.",
        choice_answer="The friends divided their meal fairly and asked every village to help its neighbors before receiving water.",
        result_answer="Cooperation opened all three gates and established fair water levels in every channel.",
    ),
]


OPENINGS = [
    "Long before maps had names, {hero} and {friend} came to {setting} carrying one warm shishkebab between them.",
    "Hear now a myth from {setting}: {hero} bore a shishkebab, and {friend} walked beside {hero} as a trusted friend.",
    "In the elder days, smoke from {hero} and {friend}'s shishkebab was the only warm thread above {setting}.",
    "The oldest stones of {setting} remember two friends, {hero} and {friend}, and the shishkebab they promised to share.",
]


def _stable_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = "|".join((params.setting, params.hero, params.friend, params.giver))
    return sum((i + 1) * ord(ch) for i, ch in enumerate(text))


def _fill(text: str, facts: dict[str, object]) -> str:
    return text.format(**facts)


def _sentence_start(text: str) -> str:
    return text[:1].upper() + text[1:]


def _story_lines(world: World) -> list[str]:
    f = world.facts
    arc: MythArc = f["arc"]
    opening = _fill(OPENINGS[f["prose_variant"]], f)
    premise = _fill(arc.premise, f)
    problem = _fill(arc.problem, f)
    choice = _fill(arc.choice, f)
    action = _fill(arc.action, f)
    result = _fill(arc.result, f)
    ending = _fill(arc.ending, f)
    hero = f["hero"]
    friend = f["friend"]
    giver = f["giver"]
    giver_at_start = _sentence_start(giver)
    theme = "ice, living fluid, friendship, and kindness"

    structures = [
        [
            f"{opening} This is the tale called \"{arc.title}.\"",
            f"{premise} {problem}",
            f"{giver_at_start} watched in silence. {choice}",
            action,
            f"{result} The spirit said, \"Kindness is strongest when friendship makes room for one more.\"",
            f"At dusk, {ending}. So the people remembered a myth of {theme}.",
        ],
        [
            opening,
            f"\"Why has the cold done this?\" {friend} asked. {premise}",
            _sentence_start(problem),
            f"{giver_at_start} offered no command, only a choice. {choice}",
            f"First they listened; then they acted. {action} {result}",
            f"Years later, people still named it \"{arc.title},\" and painted {ending}. The painting honored {theme}.",
        ],
        [
            f"Whenever elders tell \"{arc.title},\" they begin with a scent: the warm shishkebab carried by {hero} and {friend} through {f['setting']}.",
            premise,
            f"Then came the trouble. {problem}",
            f"\"We decide together,\" said {hero}. {choice}",
            f"What followed was patient work, not a battle: {action[0].lower() + action[1:]}",
            result,
            f"That night, {ending}. From then on, children linked ice and fluid with friendship and kindness, not fear.",
        ],
        [
            f"{opening} They did not yet know that the day would be remembered as \"{arc.title}.\"",
            f"The first sign was strange. {problem}",
            f"Only then did {giver} reveal the old truth: {premise[0].lower() + premise[1:]}",
            choice,
            f"{friend} asked, \"Will this help everyone?\" {hero} nodded, and {action[0].lower() + action[1:]}",
            f"Their answer came in what changed: {result[0].lower() + result[1:]}",
            f"No treasure marked their victory. Instead, {ending}. It became a sign of {theme}.",
        ],
        [
            f"{opening} \"Share the fire, share the road,\" {friend} reminded {hero}.",
            f"In those days, {premise[0].lower() + premise[1:]} But {problem[0].lower() + problem[1:]}",
            f"Many would have hurried past. The two friends stopped. {choice}",
            action,
            f"{giver_at_start} bowed. {result} \"You have answered cold with care,\" the spirit said.",
            f"The proof remained after words were gone: {ending}. Thus grew a myth about {theme}.",
        ],
        [
            f"The ending of \"{arc.title}\" can still be seen in carvings: {ending}.",
            f"The carving remembers {hero} and {friend}. {opening}",
            f"Their journey mattered because {premise[0].lower() + premise[1:]} Soon, {problem[0].lower() + problem[1:]}",
            f"{giver_at_start} asked, \"What will you protect first: yourselves, or your bond with others?\" {choice}",
            action,
            f"{result} That is why the carving means {theme}, rather than victory by force.",
        ],
    ]
    return structures[f["structure_variant"]]

# Inline ASP twin: a simple parity-checkable rule set.
ASP_RULES = r"""
setting(cold_valley).
setting(moonlit_spring).
setting(frozen_grove).

feature(friendship).
feature(kindness).

can_tell_story(S) :- setting(S).
can_tell_story(S) :- setting(S), feature(friendship), feature(kindness).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTING_REGISTRY:
        key = s.replace("the ", "").replace(" ", "_")
        lines.append(asp.fact("setting", key))
    lines.append(asp.fact("feature", "friendship"))
    lines.append(asp.fact("feature", "kindness"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic shishkebab, ice, and fluid story world.")
    ap.add_argument("--setting", choices=list(SETTING_REGISTRY))
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--giver")
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
    setting = args.setting or rng.choice(list(SETTING_REGISTRY))
    hero = args.hero or rng.choice(["Ari", "Nima", "Oren", "Ilo", "Sera"])
    friend = args.friend or rng.choice(["Mira", "Tavi", "Luma", "Rin", "Kio"])
    giver = args.giver or rng.choice(["the river spirit", "the frost elder", "the spring nymph"])
    if hero == friend:
        raise StoryError("The hero and friend must be different characters.")
    return StoryParams(setting=setting, hero=hero, friend=friend, giver=giver)


def generate(params: StoryParams) -> StorySample:
    seed = _stable_seed(params)
    arc = MYTH_ARCS[seed % len(MYTH_ARCS)]
    world = World(setting=params.setting)
    hero = world.add(Entity(name=params.hero, kind="character", memes={"friendship": 1.0}))
    friend = world.add(Entity(name=params.friend, kind="character", memes={"kindness": 1.0}))
    giver = world.add(
        Entity(
            name=params.giver,
            kind="spirit",
            meters={"fluid": 1.0},
            memes={"judgment": 1.0},
        )
    )
    world.add(Entity(name="the shared shishkebab", kind="food", meters={"warmth": 1.0}))
    world.add(Entity(name="the mythic ice", kind="substance", meters={"frozen": 1.0}))
    world.add(Entity(name="the flowing fluid", kind="substance", meters={"flow": 0.0}))
    hero.memes["kindness"] = 1.0
    friend.memes["friendship"] = 1.0
    world.facts.update(
        hero=hero.name,
        friend=friend.name,
        giver=giver.name,
        setting=params.setting,
        arc=arc,
        arc_title=arc.title,
        prose_variant=(seed // (len(MYTH_ARCS) * 6)) % len(OPENINGS),
        structure_variant=(seed // len(MYTH_ARCS)) % 6,
        problem=_fill(arc.problem, {"hero": hero.name, "friend": friend.name, "giver": giver.name, "setting": params.setting}),
        kindness_choice=_fill(arc.choice, {"hero": hero.name, "friend": friend.name, "giver": giver.name, "setting": params.setting}),
        causal_action=_fill(arc.action, {"hero": hero.name, "friend": friend.name, "giver": giver.name, "setting": params.setting}),
        resolution=_fill(arc.result, {"hero": hero.name, "friend": friend.name, "giver": giver.name, "setting": params.setting}),
        ending_image=_fill(arc.ending, {"hero": hero.name, "friend": friend.name, "giver": giver.name, "setting": params.setting}),
        theme="shishkebab, ice, fluid, friendship, kindness",
    )
    story = "\n\n".join(_story_lines(world))
    prompts = [
        f"Write a short myth about {params.hero}, {params.friend}, and a shishkebab in {params.setting}.",
        f"Tell a gentle legend where ice and fluid test friendship and kindness.",
        "Write a child-facing myth in which sharing food changes a cold place.",
    ]
    story_qa = [
        QAItem(
            question=f"What danger or need did {params.hero} and {params.friend} face in \"{arc.title}\"?",
            answer=arc.problem_answer,
        ),
        QAItem(
            question="How did the friends choose kindness instead of an easier or selfish path?",
            answer=arc.choice_answer,
        ),
        QAItem(
            question=f"What changed because of {params.hero} and {params.friend}'s action?",
            answer=arc.result_answer,
        ),
        QAItem(
            question=f"What final image closes the myth of {arc.title}?",
            answer=f"The myth ends with an image of {world.facts['ending_image']}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is kindness?",
            answer="Kindness is when someone chooses to help, share, or be gentle with others."
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is the caring bond between people who help and enjoy each other."
        ),
        QAItem(
            question="What is ice?",
            answer="Ice is frozen water, and it can feel very cold and hard."
        ),
        QAItem(
            question="What is fluid?",
            answer="A fluid is something that can flow, like water or other liquids."
        ),
        QAItem(
            question="What is a shishkebab?",
            answer="A shishkebab is food cooked on a skewer, often with small pieces of meat or vegetables."
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world trace ---")
        for e in sample.world.entities.values():
            print(f"{e.name}: kind={e.kind}, meters={dict(e.meters)}, memes={dict(e.memes)}")
    if qa:
        print()
        print("== prompts ==")
        for p in sample.prompts:
            print(p)
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def _valid_python() -> list[str]:
    return sorted(s.replace("the ", "").replace(" ", "_") for s in SETTING_REGISTRY)


def _asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show can_tell_story/1."))
    return sorted(set(asp.atoms(model, "can_tell_story")))


def asp_verify() -> int:
    py = {(s,) for s in _valid_python()}
    cl = set(_asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches python ({len(py)} settings).")
        return 0
    print("MISMATCH between clingo and python:")
    print("python only:", sorted(py - cl))
    print("clingo only:", sorted(cl - py))
    return 1


def generation_prompts(sample: StorySample) -> list[str]:
    return sample.prompts


def build_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show can_tell_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for item in _asp_valid():
            print(item[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in SETTING_REGISTRY:
            params = StoryParams(setting=setting, hero="Ari", friend="Mira", giver="the river spirit")
            samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = build_story_params(args, rng)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
