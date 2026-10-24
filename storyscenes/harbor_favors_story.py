"""Compose requests for tools through three characters' independent projects.

The bounded controller follows enacted replies, not a selected whole-plot ID.
It is an authored policy over a small workshop, not a general character planner.
Every loan and return uses the shared physical protocol; no runtime LLM is used.
"""
from dataclasses import asdict, dataclass, replace
import argparse
import json
import random

from .capabilities.api import registry as base_registry
from .capabilities.core import Action, CapabilityError, Entity, Query, Record, WorldSpec, execute, fingerprint, plain, replay
from .capabilities.epistemic import Attention, Channel, Exposure, Fact, Proposition, Result
from .capabilities.physical import Container, Grant, LoanTerms, Ownership, Parent, location
from .capabilities.reading import Reader

ACTORS = ("ari", "bo", "cy")
KINDS = ("boat", "flags", "chart")
TOOLS = ("rope", "scissors", "lantern")
NEED = dict(zip(KINDS, TOOLS))
POLICIES = ("lend_first", "work_first", "reciprocate")


@dataclass(frozen=True, kw_only=True)
class Project(Record):
    kind: str


@dataclass(frozen=True, kw_only=True)
class LendingPolicy(Record):
    mode: str
    relaxed_event: str | None = None


@dataclass(frozen=True, kw_only=True)
class Inquiry(Record):
    borrower: str
    owner: str
    tool: str
    asked_event: str
    response: str = "pending"
    reply_event: str | None = None
    heard_by: tuple[str, ...] = ()


@dataclass(frozen=True, kw_only=True)
class WorkResult(Record):
    kind: str
    event_id: str


@dataclass(frozen=True, kw_only=True)
class SessionResult(Record):
    completed: bool
    event_id: str


def waiting_cycle(state):
    """A cycle of latest, enacted wait replies, not speculative search failure."""
    latest = {}
    rows = state.all("favor_inquiries") if hasattr(state, "all") else state.tables["favor_inquiries"].values()
    for row in rows:
        latest[row.borrower] = row
    get = state.maybe if hasattr(state, "maybe") else state.get
    edges = {actor: row for actor, row in latest.items()
             if row.response == "wait" and get("favor_results", actor) is None}
    for start in ACTORS:
        chain = []
        node = start
        while node in edges and node not in chain:
            chain.append(node)
            node = edges[node].owner
        if node in chain:
            return tuple(edges[a] for a in chain[chain.index(node):])
    return ()


def ask_tool(tx, *, inquiry):
    actor = tx.action.actor
    tool = NEED[tx.get("favor_projects", actor).kind]
    owner = tx.get("ownership", tool).owner
    tx.require(location(tx, actor) == location(tx, owner), "The finite request must be heard in person")
    tx.require(actor != owner and tx.maybe("favor_results", actor) is None, "Only an unfinished project needs this loan")
    tx.require(tx.maybe("favor_inquiries", inquiry) is None, "Inquiry identity already used")
    tx.put("favor_inquiries", Inquiry(id=inquiry, borrower=actor, owner=owner, tool=tool, asked_event=tx.event_id))
    tx.emit(borrower=actor, owner=owner, tool=tool)


def reply_tool(tx, *, inquiry):
    row = tx.get("favor_inquiries", inquiry)
    tx.require(row.owner == tx.action.actor and row.response == "pending", "Only the addressed owner may answer")
    tx.require(location(tx, row.owner) == location(tx, row.borrower), "The reply must be heard in person")
    policy = tx.get("favor_policies", row.owner)
    ready = (policy.mode == "lend_first" or policy.relaxed_event is not None
             or tx.maybe("favor_results", row.owner) is not None)
    heard_by = tuple(actor for actor in ACTORS if location(tx, actor) == location(tx, row.owner))
    tx.depend(row.asked_event)
    tx.put("favor_inquiries", replace(row, response="ready" if ready else "wait",
                                     reply_event=tx.event_id, heard_by=heard_by))
    tx.emit(inquiry=inquiry, response="ready" if ready else "wait", owner=row.owner,
            borrower=row.borrower, owner_project=tx.get("favor_projects", row.owner).kind)


def relax_priority(tx):
    policy = tx.get("favor_policies", tx.action.actor)
    cycle = waiting_cycle(tx)
    tx.require(policy.mode == "reciprocate" and policy.relaxed_event is None,
               "Only a reciprocal policy may change its first-work demand")
    participants = {row.borrower for row in cycle}
    tx.require(tx.action.actor in participants, "A visible waiting cycle is required")
    tx.require(len({location(tx, row.borrower) for row in cycle}) == 1, "The waiting participants must be together")
    tx.require(all(participants <= set(row.heard_by) for row in cycle),
               "The shared waiting cycle requires hearing each reply, not just meeting afterward")
    for row in cycle:
        tx.depend(row.reply_event)
    tx.put("favor_policies", replace(policy, relaxed_event=tx.event_id))
    tx.emit(cycle=tuple(row.borrower for row in cycle), actor=tx.action.actor)


def complete_work(tx):
    actor = tx.action.actor
    project = tx.get("favor_projects", actor)
    tx.require(tx.maybe("favor_results", actor) is None, "Project already complete")
    tx.depend(f"use_{actor}:1")
    tool = NEED[project.kind]
    tx.require(tx.get("parents", tool).parent == actor, "Completion requires actual tool custody")
    if project.kind == "boat":
        tx.depend(f"open_{actor}:1")
        tx.require(tx.get("parents", f"boat_{actor}").parent == f"tub_{actor}", "The boat must actually float in its tub")
        tx.require(tx.get("containers", f"tub_{actor}").open, "The cover must be raised")
    elif project.kind == "flags":
        tx.require(tx.get("containers", f"parcel_{actor}").open, "The flags must be unpacked")
    else:
        evidence = tx.get("evidence", f"reading_{actor}")
        tx.require(evidence.observer == actor and evidence.outcome == "exact", "The chart must actually be read")
        tx.depend(evidence.event_id)
    tx.put("favor_results", WorkResult(id=actor, kind=project.kind, event_id=tx.event_id))
    tx.emit(actor=actor, kind=project.kind)


def finish_session(tx):
    tx.require(tx.action.actor == "ari" and tx.maybe("favor_session", "end") is None, "One final session result")
    tx.require(all(loan.status == "discharged" for loan in tx.all("loans")), "Return every enacted loan before closing")
    result = tx.maybe("favor_results", "ari")
    if result is None:
        cycle = waiting_cycle(tx)
        tx.require(bool(cycle), "A stopped session needs enacted unresolved waiting, not a search cutoff")
        tx.require(not any(tx.get("favor_policies", row.borrower).mode == "reciprocate"
                           and tx.get("favor_policies", row.borrower).relaxed_event is None for row in cycle),
                   "The authored reciprocal option has not yet been tried")
        for row in cycle:
            tx.depend(row.reply_event)
    else:
        tx.depend(result.event_id)
    tx.put("favor_session", SessionResult(id="end", completed=result is not None, event_id=tx.event_id))
    tx.emit(completed=result is not None)


def registry():
    reg = base_registry()
    for name, cls in (("favor_projects", Project), ("favor_policies", LendingPolicy),
                      ("favor_inquiries", Inquiry), ("favor_results", WorkResult), ("favor_session", SessionResult)):
        reg.table(name, cls)

    def validate(state):
        if set(state.tables["favor_projects"]) != set(ACTORS) or set(state.tables["favor_policies"]) != set(ACTORS):
            raise CapabilityError("Each physical actor needs exactly one project and policy")
        for actor in ACTORS:
            if state.get("entities", actor).kind != "actor" or state.get("favor_projects", actor).kind not in KINDS:
                raise CapabilityError("Project must bind to an actor and known task")
            if state.get("favor_policies", actor).mode not in POLICIES:
                raise CapabilityError("Unknown lending policy")

    def initial(state):
        if any(state.tables[name] for name in ("favor_inquiries", "favor_results", "favor_session")):
            raise CapabilityError("Favors must be enacted, not preloaded")
        if any(p.relaxed_event for p in state.tables["favor_policies"].values()):
            raise CapabilityError("Changed priorities must be enacted")

    reg.validators.append(validate)
    reg.initial_validators.append(initial)
    reg.operation("ask_favor_tool", ask_tool, reads={"favor_projects", "favor_results", "ownership", "favor_inquiries", "entities", "parents"}, writes={"favor_inquiries"})
    reg.operation("reply_favor_tool", reply_tool, reads={"favor_inquiries", "favor_policies", "favor_results", "favor_projects", "entities", "parents"}, writes={"favor_inquiries"})
    reg.operation("relax_favor_priority", relax_priority, reads={"favor_inquiries", "favor_policies", "favor_results", "entities", "parents"}, writes={"favor_policies"})
    reg.operation("complete_favor_work", complete_work, reads={"favor_projects", "favor_results", "parents", "containers", "evidence"}, writes={"favor_results"})
    reg.operation("finish_favor_session", finish_session, reads={"favor_session", "favor_results", "favor_inquiries", "favor_policies", "loans"}, writes={"favor_session"})
    return reg


@dataclass(frozen=True, kw_only=True)
class Conditions:
    projects: tuple[str, ...] = ("boat", "flags", "chart")
    owners: tuple[str, ...] = ("bo", "cy", "ari")
    policies: tuple[str, ...] = ("work_first", "reciprocate", "work_first")

    def __post_init__(self):
        for values, choices in ((self.projects, KINDS), (self.owners, ACTORS), (self.policies, POLICIES)):
            if len(values) != 3 or any(v not in choices for v in values):
                raise ValueError("Provide three valid project, tool-owner and policy values")


def conditions(seed):
    rng = random.Random(seed)
    projects = tuple(rng.choice(KINDS) for _ in ACTORS)
    owners = list(rng.choice(ACTORS) for _ in TOOLS)
    owners[TOOLS.index(NEED[projects[0]])] = rng.choice(("bo", "cy"))
    return Conditions(projects=projects, owners=tuple(owners), policies=tuple(rng.choice(POLICIES) for _ in ACTORS))


def build(c):
    entities = [Entity(id=a, name=a.capitalize(), kind="actor", capacity=30) for a in ACTORS]
    entities.append(Entity(id="workshop", name="the harbor workshop", kind="place"))
    entities.extend(Entity(id=t, name={"rope": "the rope", "scissors": "the scissors", "lantern": "the lantern"}[t], kind="object") for t in TOOLS)
    parents = [Parent(id=a, parent="workshop") for a in ACTORS]
    parents.extend(Parent(id=t, parent=owner) for t, owner in zip(TOOLS, c.owners))
    containers, facts, propositions, exposures, attention = [], [], [], [], []
    actions, terms, grants = [], [], []

    def q(table, key, field, value):
        return Query(table=table, key=key, field=field, value=value)

    def add(action_id, op, actor, *, requires=(), **args):
        actions.append(Action(id=action_id, operation=op, actor=actor, args=args, requires=requires))

    for actor, kind in zip(ACTORS, c.projects):
        tool = NEED[kind]
        owner = c.owners[TOOLS.index(tool)]
        held = (q("parents", tool, "parent", actor),)
        if kind == "boat":
            entities.extend((Entity(id=f"boat_{actor}", name=f"{actor.capitalize()}'s little boat", kind="object"),
                             Entity(id=f"tub_{actor}", name=f"{actor.capitalize()}'s covered water tub", kind="container", capacity=30)))
            parents.extend((Parent(id=f"boat_{actor}", parent=actor), Parent(id=f"tub_{actor}", parent="workshop")))
            containers.append(Container(id=f"tub_{actor}", open=False))
            add(f"open_{actor}", "set_container", actor, container=f"tub_{actor}", open=True, requires=held)
            add(f"use_{actor}", "put", actor, object=f"boat_{actor}", destination=f"tub_{actor}", requires=held)
        elif kind == "flags":
            entities.extend((Entity(id=f"parcel_{actor}", name=f"{actor.capitalize()}'s sealed flag parcel", kind="container", capacity=20),
                             Entity(id=f"flags_{actor}", name=f"{actor.capitalize()}'s paper flags", kind="object")))
            parents.extend((Parent(id=f"parcel_{actor}", parent="workshop"), Parent(id=f"flags_{actor}", parent=f"parcel_{actor}")))
            containers.append(Container(id=f"parcel_{actor}", open=False))
            add(f"use_{actor}", "set_container", actor, container=f"parcel_{actor}", open=True, requires=held)
        else:
            entities.append(Entity(id=f"chart_{actor}", name=f"{actor.capitalize()}'s chart", kind="object"))
            parents.append(Parent(id=f"chart_{actor}", parent="workshop"))
            propositions.append(Proposition(id=f"mark_{actor}", subject=f"chart_{actor}", predicate="landing direction",
                scope="chart_inscription", result=Result(kind="exact", value="past the red buoy"), reference_start=0, reference_end=0))
            facts.append(Fact(id=f"mark_{actor}", carrier=f"chart_{actor}", proposition=f"mark_{actor}"))
            exposures.append(Exposure(id=f"view_{actor}", fact=f"mark_{actor}"))
            attention.append(Attention(id=actor, actor=actor, source=f"chart_{actor}", channel="eyes", until=100))
            add(f"use_{actor}", "observe", actor, fact=f"mark_{actor}", exposure=f"view_{actor}",
                attention=actor, channel="eyes", evidence=f"reading_{actor}", requires=held)
        add(f"done_{actor}", "complete_favor_work", actor)
        add(f"relax_{actor}", "relax_favor_priority", actor)
        if owner == actor:
            continue
        loan = f"loan_{actor}"
        terms.append(LoanTerms(id=loan, version=1, object=tool, owner=owner, lender=owner, borrower=actor,
            source=owner, return_authority=owner, return_recipient=owner, return_destination=owner))
        grants.append(Grant(id=f"settle_{actor}", issuer=owner, grantee=owner, object=tool,
            right="settle", scope=loan, destination=owner))
        for attempt in range(1, 4):
            inquiry = f"{actor}_{attempt}"
            add(f"ask_{inquiry}", "ask_favor_tool", actor, inquiry=inquiry)
            add(f"reply_{inquiry}", "reply_favor_tool", owner, inquiry=inquiry)
            add(f"offer_{inquiry}", "offer_loan", owner, id=loan, terms=loan, version=1, loan_id=loan,
                requires=(q("favor_inquiries", inquiry, "response", "ready"),))
        add(f"understand_{actor}", "comprehend_loan", actor, offer=loan, version=1)
        add(f"accept_{actor}", "respond_loan", actor, offer=loan, version=1)
        add(f"ready_{actor}", "readiness", actor, id=loan, giver=owner, object=tool, operation="activate_loan")
        add(f"borrow_{actor}", "activate_loan", actor, offer=loan, version=1, readiness_id=loan)
        add(f"return_offer_{actor}", "offer_return", actor, id=loan, loan_id=loan, object=tool,
            recipient=owner, destination=owner, version=1, requires=(q("favor_results", actor, "id", actor),))
        add(f"return_accept_{actor}", "respond_return", owner, offer=loan, version=1)
        add(f"return_ready_{actor}", "readiness", owner, id=f"return_{actor}", giver=actor, object=tool, operation="complete_return")
        add(f"return_{actor}", "complete_return", actor, offer=loan, version=1, readiness_id=f"return_{actor}")
    add("finish", "finish_favor_session", "ari")
    records = dict(entities=tuple(entities), parents=tuple(parents), containers=tuple(containers),
        ownership=tuple(Ownership(id=t, owner=o) for t,o in zip(TOOLS, c.owners)), loan_terms=tuple(terms), grants=tuple(grants),
        favor_projects=tuple(Project(id=a, kind=k) for a,k in zip(ACTORS,c.projects)),
        favor_policies=tuple(LendingPolicy(id=a, mode=p) for a,p in zip(ACTORS,c.policies)),
        propositions=tuple(propositions), facts=tuple(facts), exposures=tuple(exposures), attention=tuple(attention),
        channels=(Channel(id="eyes", kind="observation"),))
    return WorldSpec(title="Who goes first?", records=records, actions=tuple(actions),
                     goal=(q("favor_session", "end", "id", "end"),), max_steps=150)


def generate(seed=0, *, config=None, prose_seed=None):
    from .harbor_favors_prose import render
    c = conditions(seed) if config is None else config
    spec, reg = build(c), registry()
    state = reg.initial(spec)
    actions = {a.id: a for a in spec.actions}
    attempts = {a: 0 for a in ACTORS}

    def do(id):
        nonlocal state
        after = execute(reg, spec, state, actions[id])
        if after is None:
            raise CapabilityError(f"Illegal favor continuation: {id}")
        state = after

    def work(actor, active=()):
        if state.get("favor_results", actor):
            return True
        if actor in active:
            return False
        tool = NEED[state.get("favor_projects", actor).kind]
        owner = state.get("ownership", tool).owner
        if owner != actor:
            # A still-current wait reply already supplies the dependency.
            # Resume that work instead of narrating the same request again.
            previous = next((r for r in reversed(tuple(state.tables["favor_inquiries"].values())) if r.borrower == actor), None)
            policy = state.get("favor_policies", owner)
            if (previous and previous.response == "wait" and not state.get("favor_results", owner)
                    and policy.mode != "lend_first" and policy.relaxed_event is None):
                if not work(owner, active + (actor,)):
                    return False
            while True:
                attempts[actor] += 1
                if attempts[actor] > 3:
                    raise CapabilityError("Explicit favor attempt bound exhausted")
                inquiry = f"{actor}_{attempts[actor]}"
                do(f"ask_{inquiry}")
                do(f"reply_{inquiry}")
                if state.get("favor_inquiries", inquiry).response == "ready":
                    do(f"offer_{inquiry}")
                    for step in ("understand", "accept", "ready", "borrow"):
                        do(f"{step}_{actor}")
                    break
                if not work(owner, active + (actor,)):
                    return False
        if state.get("favor_projects", actor).kind == "boat":
            do(f"open_{actor}")
        do(f"use_{actor}")
        do(f"done_{actor}")
        if owner != actor:
            for step in ("return_offer", "return_accept", "return_ready", "return"):
                do(f"{step}_{actor}")
        return True

    while not work("ari"):
        cycle = waiting_cycle(state)
        flexible = next((r.borrower for r in cycle if state.get("favor_policies", r.borrower).mode == "reciprocate"
                         and state.get("favor_policies", r.borrower).relaxed_event is None), None)
        if flexible is None:
            break
        do(f"relax_{flexible}")
    do("finish")
    path = [e.action.id for e in state.events]
    if replay(reg, spec, path) != state:
        raise CapabilityError("Favor network did not replay")
    doc = render(spec, state)
    row = dict(ok=True, world="harbor_favors", sample_id=f"harbor_favors:{seed}", seed=seed,
        conditions=asdict(c), story=doc.story, words=len(doc.story.split()), path=path,
        trace_sha256=fingerprint(state), qa=[plain(q) for q in Reader(doc).questions()],
        plot=dict(purpose=state.get("favor_projects", "ari").kind,
                  outcome="completed" if state.get("favor_session", "end").completed else "waiting",
                  completed_projects=[r.id for r in state.tables["favor_results"].values()],
                  waiting_replies=sum(r.response == "wait" for r in state.tables["favor_inquiries"].values()),
                  changed_priority=[p.id for p in state.tables["favor_policies"].values() if p.relaxed_event],
                  loans=len(state.tables["loans"])))
    return row, spec, state, doc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--qa", action="store_true")
    args = parser.parse_args()
    row = generate(args.seed)[0]
    print(row["story"])
    if args.qa:
        print(json.dumps(row["qa"], indent=2))


if __name__ == "__main__":
    main()
