from functools import wraps
from dataclasses import dataclass, field
from typing import List, Optional
import json


# Shapes that read as an identity check. Kept module level so a rule can extend
# the judgement rather than restate it.
GUARD_PREFIXES = ("check_", "assert_", "validate_", "verify_")
GUARD_SUBJECTS = ("own", "account", "key", "mint", "program", "authority", "signer", "address")
REQUIRE_MACROS = ("require", "require_eq", "require_keys_eq", "require_keys_neq")

# Types that make a binding an account rather than an ordinary local.
ACCOUNT_TYPES = {
    "AccountInfo", "UncheckedAccount", "Account", "AccountLoader", "Signer",
    "Program", "SystemAccount", "InterfaceAccount", "Sysvar",
}


def _guard_name_mentions(ident, against) -> bool:
    """`check_account_owner` states its subject in the name, not the arguments."""
    lowered = (ident or "").lower()
    return any(word.lower().strip("_") in lowered for word in (against or ()))


def _names_an_identity_guard(ident) -> bool:
    """Does this function name read as "prove something about an account"?"""
    if not ident:
        return False
    lowered = ident.lower()
    if not any(lowered.startswith(prefix) for prefix in GUARD_PREFIXES):
        return False
    return any(subject in lowered for subject in GUARD_SUBJECTS)


class RuleSkip(Exception):
    """Control-flow signal: abandon this item, not the rule.

    `exit_on_none` / `exit_on_value` raise this to tell a rule's loop body that
    the item under inspection is not interesting. It is deliberately its own
    type rather than a generic error, because every template guards its loop
    with a handler, and a handler that catches everything also catches the
    rule's own bugs - an unhashable value in a set, a builtin the sandbox does
    not expose - which turns a broken rule into a scan that reports nothing.
    A rule that dies then reads exactly like a rule that found nothing.

    `SandboxTransformer.visit_ExceptHandler` narrows every bare `except:` in a
    template to this type, so anything else propagates to `run_scan_task`,
    which records the error and makes the controller exit non-zero.
    """


def dsl_log(func):
    """Decorator for logging DSL function calls and their results.

    Args:
        func: The function to be decorated.

    Returns:
        Wrapped function that logs its execution details.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        args_str = ", ".join(
            str(arg)[:50] + "..." if len(str(arg)) > 50 else str(arg)
            for arg in args[1:]
        )
        kwargs_str = ", ".join(
            f"{k}={str(v)[:30] + '...' if len(str(v)) > 30 else str(v)}"
            for k, v in kwargs.items()
        )
        params = ", ".join(filter(None, [args_str, kwargs_str]))

        try:
            result = func(*args, **kwargs)

            node_count = 0
            if hasattr(result, "__len__"):
                node_count = len(result)
            elif result is not None:
                node_count = 1

            # Special handling for exit methods
            if func_name == "exit_on_none":
                print(
                    f"[d] [dsl_log] {func_name}({params}) -> continued ({node_count} nodes)"
                )  # should always be >1
            elif func_name == "exit_on_value":
                print(
                    f"[d] [dsl_log] {func_name}({params}) -> continued ({node_count} nodes)"
                )  # should always be 0
            else:
                print(f"[d] [dsl_log] {func_name}({params}) -> {node_count} nodes")
            return result
        except RuleSkip as e:
            print(f"[d] [dsl_log] {func_name}({params}) -> RuleSkip: {e}")
            raise

    return wrapper


class ASTNodeListGroup:
    def __init__(self, node_lists):
        self.node_lists = node_lists if isinstance(node_lists, list) else [node_lists]

    def __getattr__(self, name):
        def method(*args, **kwargs):
            results = []
            for node_list in self.node_lists:
                method = getattr(node_list, name, None)
                if method:
                    result = method(*args, **kwargs)
                    if isinstance(result, ASTNodeList):
                        results.extend(result.nodes)
                    elif result is not None:
                        results.append(result)
            return ASTNodeList(results)

        return method

    def __iter__(self):
        return iter(self.node_lists)

    def __len__(self):
        return len(self.node_lists)

    def __getitem__(self, index):
        return self.node_lists[index]

    @dsl_log
    def to_result(self):
        """Convert the node list group to result format.

        Returns:
            List of result dictionaries for each node list in the group.
        """
        return [node_list.to_result() for node_list in self.node_lists]

    @dsl_log
    def first(self):
        """Get the first node list in the group.

        Returns:
            The first node list in the group, or raises RuleSkip if empty.
        """
        return self.node_lists[0] if self.node_lists else self.exit_on_none()

    @dsl_log
    def exit_on_none(self):
        """Exit with RuleSkip if no node lists are found.

        Returns:
            Self if node lists exist.

        Raises:
            RuleSkip: If no node lists are found.
        """
        if not self.node_lists:
            raise RuleSkip("No node lists found")
        return self

    @dsl_log
    def exit_on_value(self):
        """Exit with RuleSkip if node lists are found.

        Returns:
            Self if no node lists exist.

        Raises:
            RuleSkip: If node lists are found.
        """
        if self.node_lists:
            raise RuleSkip("Node lists found")
        return self

    def to_raw_ast_debug(self):
        """Print debug information for the node list group.

        Returns:
            Self for method chaining.
        """
        result_data = []
        for i, node_list in enumerate(self.node_lists):
            group_data = []
            for node in node_list.nodes:
                group_data.append(node.to_result())
            result_data.append(group_data)

        print()
        print("Raw AST Node List Group Debug:")
        print(json.dumps(result_data, indent=4, default=str))
        print()
        return self


class ASTNodeList:
    def __init__(self, nodes):
        self.nodes = nodes if isinstance(nodes, list) else [nodes]

    def __getattr__(self, name):
        def method(*args, **kwargs):
            results = []
            for node in self.nodes:
                node_method = getattr(node, name, None)
                if node_method:
                    result = node_method(*args, **kwargs)
                    if isinstance(result, list):
                        results.extend(result)
                    elif isinstance(result, ASTNodeList):
                        results.extend(result.nodes)
                    elif result is not None:
                        results.append(result)
            return ASTNodeList(results)

        return method

    def __iter__(self):
        return iter(self.nodes)

    def __len__(self):
        return len(self.nodes)

    def __getitem__(self, index):
        return self.nodes[index]

    @dsl_log
    def to_result(self):
        """Convert the node list to result format.

        Returns:
            List of result dictionaries for each node in the list.
        """
        return [node.to_result() for node in self.nodes]

    @dsl_log
    def first(self):
        """Get the first node in the list.

        Returns:
            The first node in the list, or raises RuleSkip if empty.
        """
        return self.nodes[0] if self.nodes else self.exit_on_none()

    @dsl_log
    def exit_on_none(self):
        """Exit with RuleSkip if no nodes are found.

        Returns:
            Self if nodes exist.

        Raises:
            RuleSkip: If no nodes are found.
        """
        if not self.nodes:
            raise RuleSkip("No nodes found")
        return self

    @dsl_log
    def exit_on_value(self):
        """Exit with RuleSkip if nodes are found.

        Returns:
            Self if no nodes exist.

        Raises:
            RuleSkip: If nodes are found.
        """
        if self.nodes:
            raise RuleSkip("Nodes found")
        return self

    def to_raw_ast_debug(self):
        """Print debug information for the node list.

        Returns:
            Self for method chaining.
        """
        result_data = [node.to_result() for node in self.nodes]

        print()
        print("Raw AST Node List Debug:")
        print(json.dumps(result_data, indent=4, default=str))
        print()
        return self


@dataclass
class ASTNode:
    src: Optional[str | dict] = None
    access_path: str = ""
    metadata: dict = field(default_factory=dict)
    children: List["ASTNode"] = field(default_factory=list)
    parent: Optional["ASTNode"] = None
    root: bool = False

    def __init__(self, node=None, access_path="", metadata=None):
        if node:
            self.src = node.get("src")
        else:
            self.root = True

        # A fresh dict per node. A shared `metadata={}` default would alias one
        # dict across every node built without explicit metadata, so any later
        # write (node.metadata[...] = ...) would leak to all of them.
        self.metadata = metadata if metadata is not None else {}
        self.children = []
        self.access_path = access_path

    def add_child(self, child: "ASTNode"):
        """Add a child node to this node.

        Args:
            child: The child ASTNode to add.
        """
        child.parent = self
        self.children.append(child)

    def to_result(self):
        """Convert the node to result format.

        Returns:
            Dictionary representation of the node including source, children, access path, and metadata.
        """
        return {
            "src": self.src,
            "children": [child.to_result() for child in self.children],
            "access_path": self.access_path,
            "metadata": self.metadata,
        }


@dataclass
class RustASTNode(ASTNode):
    ident: str = "root"

    def __init__(self, node=None, access_path="", metadata=None):
        super().__init__(node, access_path, metadata)
        if node:
            self.ident = node.get("ident")
        else:
            self.ident = "root"
            self.root = True

    def to_result(self):
        """Convert the Rust AST node to result format.

        Returns:
            Dictionary representation of the node including identifier and parent information.
        """
        result = super().to_result()
        result.update(
            {
                "ident": self.ident,
                "parent": self.parent.ident if self.parent else None,
            }
        )
        return result

    def to_raw_ast_debug(self):
        """Print debug information for the Rust AST node.

        Returns:
            Self for method chaining.
        """
        result = super().to_result()
        result.update(
            {
                "ident": self.ident,
                "parent": self.parent.ident if self.parent else None,
            }
        )
        print()
        print("Raw AST Node Debug:")
        print(json.dumps(result, indent=4, default=str))
        print()
        return self

    @dsl_log
    def find_by_parent(self, parent_ident: str) -> ASTNodeList:
        """Find all nodes that have a specific parent identifier.

        Args:
            parent_ident: The identifier of the parent node to search for.

        Returns:
            ASTNodeList of nodes that have the specified parent identifier.
        """
        results = []
        if self.parent and self.parent.ident == parent_ident:
            results.append(self)
        for child in self.children:
            results.extend(child.find_by_parent(parent_ident))
        return ASTNodeList(results)

    @dsl_log
    def find_by_child(self, child_ident: str) -> ASTNodeList:
        """Find all nodes that have a specific child identifier.

        Args:
            child_ident: The identifier of the child node to search for.

        Returns:
            ASTNodeList of nodes that have a child with the specified identifier.
        """
        matches = []

        def recurse(node):
            if any(child.ident == child_ident for child in node.children):
                matches.append(node)
            for child in node.children:
                recurse(child)

        recurse(self)
        return ASTNodeList(matches)

    @dsl_log
    def find_chained_calls(self, *idents: tuple[str, ...]) -> ASTNodeListGroup:
        """Find sequences of chained method calls with specific identifiers.

        Args:
            *idents: Variable number of identifiers that should appear in sequence as chained calls.

        Returns:
            ASTNodeListGroup containing lists of nodes that match the chained call pattern.
        """
        matches = []

        def recurse(node, idents):
            for i in range(len(node.children) - len(idents) + 1):
                if all(
                    node.children[i + j].ident == idents[j] for j in range(len(idents))
                ):
                    matches.append(ASTNodeList(node.children[i : i + len(idents)]))
            for child in node.children:
                recurse(child, idents)

        recurse(self, idents)
        return ASTNodeListGroup(matches)

    # --- account-scope primitives --------------------------------------------
    #
    # Rules that ask "was *this* account checked" all need the same four things:
    # the identifiers under a subtree, what a `let` binding refers to, which
    # identifiers name accounts, and which of those a guard actually names.
    # Every rule that needed them used to rebuild them in its own YAML, slightly
    # differently, which is where both the false positives and the maintenance
    # cost came from - and each copy had to be written against a tree that until
    # recently dropped receiver chains, so most of them could only ask the
    # question per function.
    #
    # Asking per function is the bug: it lets a validated account excuse an
    # unvalidated sibling. These make asking per account the easy thing to write.

    def subtree_idents(self, prefix: str = "") -> set:
        """Identifiers anywhere beneath this node, optionally under an access path."""
        found = set()

        def walk(node):
            if node.ident is not None and node.access_path.startswith(prefix):
                found.add(node.ident)
            for child in node.children:
                walk(child)

        walk(self)
        return found

    def let_bindings(self) -> dict:
        """`let` name -> the identifiers its initialiser mentions.

        `let mint_data = mint_info.data.borrow();` binds `mint_data` to
        `{mint_info, data, borrow}`. A guard names `mint_info` and the unpack
        names `mint_data`, so without this hop the two never meet and every
        checked account still reports.
        """
        bindings = {}

        def walk(node):
            path = node.access_path
            if node.ident is not None and path.endswith(".let.pat.ident"):
                init_prefix = path.split(".pat.ident")[0] + ".init"
                bindings[node.ident] = self.subtree_idents(init_prefix)
            for child in node.children:
                walk(child)

        walk(self)
        return bindings

    def account_idents(self) -> set:
        """Identifiers in this scope that name an account.

        Anchor hands them over as `ctx.accounts.<name>` and as the fields of a
        `#[derive(Accounts)]` struct; native programs pull them off an iterator
        with `next_account_info`. Both spellings, because a rule that knows only
        Anchor's reports every native program that did the right thing.
        """
        names = set()

        def walk(node):
            path = node.access_path
            if node.ident is not None:
                # `let x = next_account_info(iter)?` and `let x = &ctx.accounts.y`
                if path.endswith(".let.pat.ident"):
                    init = self.subtree_idents(path.split(".pat.ident")[0] + ".init")
                    if init & {"next_account_info", "accounts"}:
                        names.add(node.ident)
                # A typed parameter, but only when its type says account.
                # Every parameter counted as an account made "is this account
                # checked" a question about arbitrary locals, which reports
                # amounts and bump seeds as unvalidated accounts.
                if path.endswith(".typed.pat.ident"):
                    type_prefix = path.split(".pat.ident")[0] + ".ty"
                    if self.subtree_idents(type_prefix) & ACCOUNT_TYPES:
                        names.add(node.ident)
            for child in node.children:
                walk(child)

        walk(self)

        # The field name in `ctx.accounts.<name>` is the account itself. It is
        # the node whose *child* is `accounts`, not its child: a field chain
        # nests outermost-first, so `ctx.accounts.vault` is `vault` -> `accounts`
        # -> `ctx`. Reading it the other way collects `ctx` as the account name
        # and every real account goes unrecognised.
        def walk_fields(node):
            # Must actually be a field access. Testing only for a child named
            # `accounts` also matched `fn process(accounts: &[AccountInfo])` -
            # the commonest native Solana signature there is - and added the
            # *function's own name* to the set of accounts in scope.
            if (
                node.ident
                and (node.access_path or "").endswith(".field")
                and any(child.ident == "accounts" for child in node.children)
            ):
                names.add(node.ident)
            for child in node.children:
                walk_fields(child)

        walk_fields(self)
        return names

    def guarded_idents(self, subjects=None, against=None) -> set:
        """Identifiers that some identity check in this scope actually names.

        Three spellings, because programs use all three and a rule that accepts
        one reports the other two:

          `require_keys_eq!(token.owner, authority.key())`   Anchor's macro
          `if account.owner != program_id { return Err(..) }` an inline guard
          `check_account_owner(program_id, mint_info)?`      a named helper,
              which is what SPL, Solend, Metaplex and stake-pool actually write

        Helpers are recognised by shape rather than by a list of names, so a
        program's own `check_mint` counts: a check/assert/validate/verify prefix
        plus a word saying the check is about an account's identity rather than,
        say, a slippage bound.

        `against` narrows what the check has to be *about*. Program ownership is
        `account.owner == program_id`, and a comparison of a deserialized
        account's own `.owner` field against an authority is a different claim
        that does not prove the program owns the account. Callers that need that
        distinction pass `against=("ID", "program_id")`; callers that accept any
        identity check leave it unset.
        """
        subjects = subjects or ("owner", "key")
        guarded = set()

        def satisfies(named):
            if not (named & set(subjects)):
                return False
            return not against or bool(named & set(against))

        def walk(node):
            path, ident = node.access_path, node.ident
            if ident is not None:
                if ".call.func." in path and _names_an_identity_guard(ident):
                    named = self.subtree_idents(path.split(".func.")[0] + ".args")
                    # A helper states its subject in its name, not its arguments:
                    # `check_account_owner(program_id, mint)` never writes
                    # `owner` as an argument. Judge the name, filter the target.
                    if not against or (named & set(against)) or _guard_name_mentions(ident, against):
                        guarded.update(named)
                if ident in REQUIRE_MACROS:
                    named = self.subtree_idents(path.split(".macro")[0])
                    if satisfies(named):
                        guarded.update(named)
            for child in node.children:
                walk(child)

        walk(self)

        # An inline condition proves the same thing, for whatever it names.
        # Collected per condition rather than per node: every node inside one
        # resolves to the same prefix, so scanning per node walks the scope once
        # per node instead of once per condition.
        conditions = set()

        def walk_conditions(node):
            if ".cond." in node.access_path:
                conditions.add(node.access_path.split(".cond.")[0] + ".cond.")
            for child in node.children:
                walk_conditions(child)

        walk_conditions(self)
        for condition in conditions:
            named = self.subtree_idents(condition)
            if satisfies(named):
                guarded |= named
        return guarded

    def unguarded_accounts_at(self, call_node, subjects=None, against=None) -> set:
        """Accounts a call reads that nothing in this scope proved.

        The per-account question, in one call: which accounts do this call's
        arguments reach once `let` bindings are followed, minus the ones a guard
        names. Empty means this particular access is covered - not that the
        function checked something, somewhere.
        """
        path = call_node.access_path
        if ".func." not in path:
            return set()

        accounts = self.account_idents()
        guarded = self.guarded_idents(subjects, against)

        # Which accounts these arguments actually reach, following data aliases
        # (`let d = info.data.borrow()` names `info`).
        reads = set()
        for ident in self.subtree_idents(path.split(".func.")[0] + ".args"):
            reads |= self.alias_closure(ident) & accounts

        # Expand only the account side, and only through aliases. Expanding the
        # guard side too - or letting the closure run through
        # `next_account_info` - collapses every account pulled off one iterator
        # into the same thing, so proving one proves all of them. That is the
        # sibling bug this rule exists to catch, reintroduced one level down.
        return {a for a in reads if not (self.alias_closure(a) & guarded)}

    def parameter_names(self) -> set:
        """The names this function takes as parameters."""
        found = set()

        def walk(node):
            path = node.access_path or ""
            if node.ident and ".inputs[" in path and path.endswith(".typed.pat.ident"):
                found.add(node.ident)
            for child in node.children:
                walk(child)

        walk(self)
        return found

    def caller_supplied(self, ident, depth: int = 4) -> bool:
        """Did this value arrive from the caller rather than get chosen here?

        A parameter, or anything derived from one. The distinction matters
        because "was this account validated" is the wrong question to ask of a
        function that picked none of its accounts: `fn token_burn(mint:
        AccountInfo, .., amount: u64)` validates nothing because it decides
        nothing, and the caller is where the check belongs. Demanding one here
        reports every thin CPI wrapper in the ecosystem - which is exactly what
        `invoke_signed_unvalidated_seeds` was reporting until it learned to ask
        this.
        """
        parameters = self.parameter_names()
        if ident in parameters:
            return True

        bindings = self.let_bindings()

        # Selecting an account out of the slice is a choice this function made,
        # even though the slice itself came from the caller. That is the line
        # between a handler and a wrapper: `next_account_info(iter)` decides
        # *which* account this is, and the handler that decides is the one that
        # owes the check. Without this every native Solana handler reads as
        # having chosen nothing, since everything ultimately traces back to the
        # `accounts` parameter.
        if "next_account_info" in bindings.get(ident, set()):
            return False
        seen, frontier = {ident}, {ident}
        for _ in range(depth):
            following = set()
            for current in frontier:
                following |= bindings.get(current, set()) - seen
            if not following:
                return False
            if following & parameters:
                return True
            seen |= following
            frontier = following
        return False

    def chose_nothing(self, idents=None) -> bool:
        """Were all of these values handed to this function?

        With no arguments, asks it of the accounts the function touches. A
        function that chose nothing is not where a missing check lives.
        """
        subject = set(idents) if idents is not None else self.account_idents()
        if not subject:
            return False
        return all(self.caller_supplied(name) for name in subject)

    def bound_positions(self, node) -> dict:
        """Tuple positions a `let` destructuring actually binds, by index.

        `let (_, bump) = find_program_address(..)` binds {1: "bump"} - position
        0 is discarded. That is the difference between deriving an address to
        check a supplied account against, and deriving one only to record its
        bump: the second has no address to compare and no account to compare it
        to, so demanding a comparison reports correct initialisation code.
        """
        path = getattr(node, "access_path", "") or ""
        marker = ".let.init"
        if marker not in path:
            return {}
        prefix = path.split(marker)[0] + ".let.pat.tuple.elems["

        positions = {}
        for candidate in (self._all_nodes if hasattr(self, "_all_nodes") else []):
            candidate_path = candidate.access_path or ""
            if not candidate_path.startswith(prefix) or not candidate.ident:
                continue
            index = candidate_path[len(prefix):].split("]")[0]
            if index.isdigit() and candidate_path.endswith(".ident"):
                positions[int(index)] = candidate.ident
        return positions

    def enclosing_type_name(self) -> str:
        """The type this method hangs off, for a method in an `impl` block.

        `impl Fee { fn apply(..) }` states what `apply` computes exactly once,
        on the impl - and the type name is not an ancestor of the method in this
        tree, it sits on a sibling branch (`impl.self_ty`). Walking parents
        therefore never reaches it, which is why a rule keyed on what a function
        is *about* reads nothing on the most ordinary Rust shape there is.

        Returns None for a free function, or when the impl names no plain type.
        """
        path = self.access_path or ""
        marker = ".impl."
        if marker not in path:
            return None
        prefix = path.split(marker)[0] + ".impl.self_ty"
        best = None
        for node in (self._all_nodes if hasattr(self, "_all_nodes") else []):
            if node.access_path.startswith(prefix) and node.ident:
                # The outermost segment is the type; deeper ones are its generics.
                if best is None or len(node.access_path) < len(best.access_path):
                    best = node
        return best.ident if best is not None else None

    def statement_index(self, node) -> int:
        """Which statement of the enclosing body this node sits in.

        Several classes are about *order*, not presence: an owner check before a
        CPI says nothing about the account after it, and a rule that only asks
        whether a check exists somewhere in the handler calls that safe. Access
        paths already carry the position - `...fn.stmts[7].let.init...` - so this
        reads it out rather than adding a second traversal.

        Returns -1 when the node is not inside a statement list, which sorts
        before every real statement.
        """
        path = getattr(node, "access_path", "") or ""
        marker = ".stmts["
        if marker not in path:
            return -1
        tail = path.rsplit(marker, 1)[1]
        digits = tail.split("]")[0]
        return int(digits) if digits.isdigit() else -1

    def binding_of(self, node) -> str:
        """The `let` name this node's value flows into, if any.

        `let ix = get_instruction_relative(0, sysvar)?` -> "ix". Rules need it to
        ask whether a guard names *the thing that was just loaded*, rather than
        whether the identifier appears somewhere in the handler. Three rules in
        a row have been wrong the second way: a `program_id` comparison about
        some other account excused the instruction that was never checked.
        """
        path = getattr(node, "access_path", "")
        marker = ".let.init"
        if marker not in path:
            return None
        prefix = path.split(marker)[0] + ".let.pat.ident"
        for candidate in self._all_nodes if hasattr(self, "_all_nodes") else []:
            if candidate.access_path == prefix:
                return candidate.ident
        return None

    def alias_closure(self, ident, depth: int = 3) -> set:
        """`ident` plus every account it is another name for.

        Follows a binding to the account it names, and stops at
        `next_account_info`: that call *mints* an account rather than aliasing
        one, so two accounts taken off the same iterator are two accounts, not
        two names for the iterator.
        """
        bindings = self.let_bindings()
        accounts = self.account_idents()

        reached, frontier = {ident}, {ident}
        for _ in range(depth):
            following = set()
            for current in frontier:
                initialiser = bindings.get(current, set())
                if "next_account_info" in initialiser:
                    continue
                following |= (initialiser & accounts) - reached
            if not following:
                break
            reached |= following
            frontier = following
        return reached

    @dsl_log
    def find_by_access_path(self, access_path_part: str) -> ASTNodeList:
        """Find nodes that contain a specific part in their access path.

        Args:
            access_path_part: The partial access path string to search for.

        Returns:
            ASTNodeList of nodes whose access path contains the specified part.
        """
        matching_nodes = []

        def recurse(node):
            if access_path_part in node.access_path:
                matching_nodes.append(node)
            for child in node.children:
                recurse(child)

        recurse(self)
        return ASTNodeList(matching_nodes)

    @dsl_log
    def find_macro_attribute_by_names(self, *idents: tuple[str, ...]) -> ASTNodeList:
        """Find macro attributes by their identifier names.

        Args:
            *idents: Variable number of identifiers to search for in macro attributes.

        Returns:
            ASTNodeList of nodes that are macro attributes with the specified identifiers.
        """
        matching_nodes = []

        def search_nodes(node):
            if isinstance(node, ASTNode):
                if node.ident in idents and ".meta.list.tokens" in node.access_path:
                    matching_nodes.append(node)
                for child in node.children:
                    search_nodes(child)
            elif isinstance(node, dict):
                for key, value in node.items():
                    if isinstance(value, (dict, list)):
                        search_nodes(value)
            elif isinstance(node, list):
                for item in node:
                    search_nodes(item)

        search_nodes(self)
        return ASTNodeList(matching_nodes)

    @dsl_log
    def find_by_similar_access_path(
        self, access_path: str, stop_keyword: str
    ) -> ASTNodeList:
        """Find nodes with access paths similar to the given path, truncated at a stop keyword.

        Args:
            access_path: The base access path to compare against.
            stop_keyword: The keyword where the path should be truncated for comparison.

        Returns:
            ASTNodeList of nodes with similar access paths to the truncated base path.
        """
        index = access_path.rfind(stop_keyword)
        if index != -1:
            truncated_path = access_path[: index + len(stop_keyword)]
        else:
            truncated_path = access_path

        matching_nodes = []

        def recurse(node):
            if (
                truncated_path in node.access_path
                and node.access_path != truncated_path
            ):
                matching_nodes.append(node)
            for child in node.children:
                recurse(child)

        recurse(self)
        return ASTNodeList(matching_nodes)

    @dsl_log
    def find_comparisons_between(self, ident1: str, ident2: str):
        """Find binary comparison operations between two specific identifiers.

        Args:
            ident1: The first identifier to look for in comparisons.
            ident2: The second identifier to look for in comparisons.

        Returns:
            ASTNodeList of comparison nodes that involve both specified identifiers.
        """
        comparisons = []

        def traverse(node):
            if not node:
                return

            if (
                "cond.binary.left" in node.access_path
                or "cond.binary.right" in node.access_path
            ):
                truncated_path = (
                    node.access_path.split(".cond.binary")[0] + ".cond.binary"
                )
                if "cond.binary.left" in node.access_path:
                    left_path = truncated_path + ".right"
                    right_node = find_node_by_access_path(left_path)
                    if right_node and check_conditions(
                        node, right_node, ident1, ident2
                    ):
                        comparisons.append(ASTNodeList([node, right_node]))
                elif "cond.binary.right" in node.access_path:
                    right_path = truncated_path + ".left"
                    left_node = find_node_by_access_path(right_path)
                    if left_node and check_conditions(left_node, node, ident1, ident2):
                        comparisons.append(ASTNodeList([left_node, node]))

            for child in node.children:
                traverse(child)

        def find_node_by_access_path(access_path):
            matching_node = None

            def recurse(node):
                nonlocal matching_node
                if access_path in node.access_path:
                    matching_node = node
                    return
                for child in node.children:
                    recurse(child)

            recurse(self)
            return matching_node

        def check_conditions(left_node, right_node, ident1, ident2):
            return (
                check_ident(left_node, ident1) and check_ident(right_node, ident2)
            ) or (check_ident(left_node, ident2) and check_ident(right_node, ident1))

        def check_ident(node, ident):
            if not node:
                return False
            if node.ident == ident:
                return True
            for child in node.children:
                if check_ident(child, ident):
                    return True
            return False

        traverse(self)
        return ASTNodeList(comparisons)

    @dsl_log
    def find_comparison_involving(self, ident: str):
        """Find any comparison operations that involve a specific identifier.

        Args:
            ident: The identifier to search for in comparison operations.

        Returns:
            ASTNodeList of comparison nodes that involve the specified identifier.
        """
        comparisons = []

        def traverse(node):
            if not node:
                return

            if (
                "cond.binary.left" in node.access_path
                or "cond.binary.right" in node.access_path
                or "cond.unary" in node.access_path
            ):
                if check_ident(node, ident):
                    comparisons.append(node)

            for child in node.children:
                traverse(child)

        def check_ident(node, ident):
            if not node:
                return False
            if node.ident == ident:
                return True
            for child in node.children:
                if check_ident(child, ident):
                    return True
            return False

        traverse(self)
        return ASTNodeList(comparisons)

    @dsl_log
    def find_negative_of_operation(
        self, operation_name: str, *args: tuple
    ) -> ASTNodeList:
        """Find nodes that are NOT involved in a specific operation.

        Args:
            operation_name: The name of the operation method to exclude.
            *args: Arguments to pass to the operation method.

        Returns:
            ASTNodeList of nodes that are not part of the specified operation results.
        """
        operation = getattr(self, operation_name)
        operation_results = operation(*args)
        operation_nodes = {node for pair in operation_results for node in pair}
        non_operation_nodes = []

        def traverse(node):
            if node not in operation_nodes:
                non_operation_nodes.append(node)
            for child in node.children:
                traverse(child)

        traverse(self)
        return ASTNodeList(non_operation_nodes)

    @dsl_log
    def find_functions_by_names(self, *function_names: tuple[str, ...]) -> ASTNodeList:
        """Find function nodes by their names.

        Args:
            *function_names: Variable number of function names to search for.

        Returns:
            ASTNodeList of function nodes with the specified names.
        """
        matching_nodes = []

        def find_function(node):
            if isinstance(node, ASTNode):
                # Check if this is a function node by looking for .fn at the end of access path
                # and the ident matches one of the function names
                if node.ident in function_names and node.access_path.endswith(".fn"):
                    matching_nodes.append(node)
                for child in node.children:
                    find_function(child)
            elif isinstance(node, dict):
                for key, value in node.items():
                    find_function(value)
            elif isinstance(node, list):
                for item in node:
                    find_function(item)

        find_function(self)
        return ASTNodeList(matching_nodes)

    @dsl_log
    def find_all_functions(self) -> ASTNodeList:
        """Find all function nodes in the AST.

        Returns:
            ASTNodeList of all function nodes found.
        """
        matching_nodes = []

        def find_function(node):
            if isinstance(node, ASTNode):
                # Check if this is a function node by looking for .fn at the end of access path
                if node.access_path.endswith(".fn"):
                    matching_nodes.append(node)
                for child in node.children:
                    find_function(child)
            elif isinstance(node, dict):
                for key, value in node.items():
                    find_function(value)
            elif isinstance(node, list):
                for item in node:
                    find_function(item)

        find_function(self)
        return ASTNodeList(matching_nodes)

    @dsl_log
    def find_by_names(self, *idents: tuple[str, ...]) -> ASTNodeList:
        """Find nodes by their identifier names.

        Args:
            *idents: Variable number of identifiers to search for.

        Returns:
            ASTNodeList of nodes with the specified identifiers.
        """
        matching_nodes = []

        def search_nodes(node):
            if isinstance(node, ASTNode):
                if node.ident in idents:
                    matching_nodes.append(node)
                for child in node.children:
                    search_nodes(child)
            elif isinstance(node, dict):
                for key, value in node.items():
                    if isinstance(value, (dict, list)):
                        search_nodes(value)
            elif isinstance(node, list):
                for item in node:
                    search_nodes(item)

        search_nodes(self)
        return ASTNodeList(matching_nodes)

    @dsl_log
    def find_method_calls(self, caller: str, method: str) -> ASTNodeList:
        """Find method call nodes with specific caller and method names.

        Args:
            caller: The identifier of the object making the method call.
            method: The name of the method being called.

        Returns:
            ASTNodeList of method call nodes matching the caller and method criteria.
        """
        matching_nodes = []

        def recurse(node):
            if isinstance(node, ASTNode):
                if node.access_path.endswith("method_call") and node.ident == method:
                    if node.children and node.children[0].ident == caller:
                        matching_nodes.append(node)
                for child in node.children:
                    recurse(child)
            elif isinstance(node, dict):
                for key, value in node.items():
                    recurse(value)
            elif isinstance(node, list):
                for item in node:
                    recurse(item)

        recurse(self)
        return ASTNodeList(matching_nodes)

    @dsl_log
    def find_assignments(self, ident: str, value_ident: str) -> ASTNodeList:
        """Find assignment operations between specific identifiers.

        Args:
            ident: The identifier being assigned to (left side of assignment).
            value_ident: The identifier being assigned from (right side of assignment).

        Returns:
            ASTNodeList of assignment nodes matching the specified identifiers.
        """
        assignments = []

        def traverse(node):
            if not node:
                return

            if node.ident == ident and ".assign.left" in node.access_path:
                assignment_path = node.access_path.split(".assign.left")[0] + ".assign"
                right_node = find_node_by_access_path(assignment_path + ".right")
                if right_node and check_conditions(node, right_node, value_ident):
                    assignments.append(ASTNodeList([node, right_node]))

            for child in node.children:
                traverse(child)

        def find_node_by_access_path(access_path):
            matching_node = None

            def recurse(node):
                nonlocal matching_node
                if access_path in node.access_path:
                    matching_node = node
                    return
                for child in node.children:
                    recurse(child)

            recurse(self)
            return matching_node

        def check_conditions(left_node, right_node, value_ident):
            left_access_path = left_node.access_path.rsplit(".assign.left", 1)[0]
            right_access_path = right_node.access_path.rsplit(".assign.right", 1)[0]
            return left_access_path == right_access_path and right_node.ident == str(
                value_ident
            )

        traverse(self)
        return ASTNodeList(assignments)

    @dsl_log
    def find_mutables(self) -> ASTNodeList:
        """Find all nodes that are marked as mutable.

        Returns:
            ASTNodeList of nodes that have the 'mut' metadata flag set to True.
        """
        mutables = []

        def traverse(node):
            if isinstance(node, ASTNode):
                if hasattr(node, "metadata") and isinstance(node.metadata, dict):
                    if node.metadata.get("mut") is True:
                        mutables.append(node)
                for child in node.children:
                    traverse(child)
            elif isinstance(node, dict):
                for key, value in node.items():
                    traverse(value)
            elif isinstance(node, list):
                for item in node:
                    traverse(item)

        traverse(self)
        return ASTNodeList(mutables)

    @dsl_log
    def find_account_typed_nodes(self, ident: str) -> ASTNodeList:
        """Find nodes that are typed as accounts with a specific identifier.

        Args:
            ident: The identifier to search for in account type definitions.

        Returns:
            ASTNodeList of nodes that are account-typed with the specified identifier.
        """
        matches = []

        def ends_with_ty_path_segments(access_path):
            parts = access_path.split(".")
            segments_index = -1
            for i in range(len(parts)):
                if parts[i] == "ty" and i + 1 < len(parts) and parts[i + 1] == "path":
                    segments_index = i + 2
                    break
            if segments_index == -1:
                return False
            while segments_index < len(parts) and (
                parts[segments_index].startswith("segments[")
                or parts[segments_index] == "segments"
            ):
                segments_index += 1
            return segments_index == len(parts)

        def traverse(node):
            if isinstance(node, ASTNode):
                if ends_with_ty_path_segments(node.access_path):
                    if node.parent.ident == ident:
                        matches.append(node.parent)
                for child in node.children:
                    traverse(child)
            elif isinstance(node, dict):
                for key, value in node.items():
                    traverse(value)
            elif isinstance(node, list):
                for item in node:
                    traverse(item)

        traverse(self)
        return ASTNodeList(matches)

    @dsl_log
    def find_member_accesses(self, ident: str) -> ASTNodeList:
        """Find member access operations for a specific identifier.

        Args:
            ident: The identifier to search for in member access operations.

        Returns:
            ASTNodeList of nodes representing member accesses of the specified identifier.
        """
        member_accesses = []

        def traverse(node):
            if isinstance(node, ASTNode):
                if (
                    node
                    and node.ident == ident
                    and (
                        "tokens" in node.access_path or "call.args" in node.access_path
                    )
                ):
                    member_accesses.append(node)
                for child in node.children:
                    traverse(child)
            elif isinstance(node, dict):
                for key, value in node.items():
                    traverse(value)
            elif isinstance(node, list):
                for item in node:
                    traverse(item)

        traverse(self)
        return ASTNodeList(member_accesses)

    @dsl_log
    def find_binary_operations(self, *operators: tuple[str, ...]) -> ASTNodeList:
        """Find binary operations with specific operators.

        Args:
            *operators: Variable number of operator strings to search for (e.g., "*", "+", "-", "/").

        Returns:
            ASTNodeList of nodes that are involved in binary operations with the specified operators.
        """
        matching_nodes = []
        search_path_prefix = self.access_path if not self.root else ""
        
        all_nodes = getattr(self, "_all_nodes", [])
        if not all_nodes:
            all_nodes = [self]
        
        seen_binary_paths = set()
        for node in all_nodes:
            if search_path_prefix and not node.access_path.startswith(search_path_prefix):
                continue
            
            op = node.metadata.get("op")
            if op and op in operators:
                has_binary_child = False
                for child in node.children:
                    if child.access_path and ".binary." in child.access_path:
                        has_binary_child = True
                        break
                
                if has_binary_child:
                    binary_base_path = node.access_path
                    if binary_base_path not in seen_binary_paths:
                        matching_nodes.append(node)
                        seen_binary_paths.add(binary_base_path)

        return ASTNodeList(matching_nodes)


def _find_ident_src_path(data, access_path):
    """Access path of the first ident-bearing node in `data`, in walk order.

    Used to decide which node a wrapper's `mut` flag belongs to.
    """
    if isinstance(data, dict):
        if "src" in data and "ident" in data:
            return access_path
        for key, value in data.items():
            new_path = f"{access_path}.{key}" if access_path else key
            found = _find_ident_src_path(value, new_path)
            if found is not None:
                return found
    elif isinstance(data, list):
        for i, item in enumerate(data):
            found = _find_ident_src_path(item, f"{access_path}[{i}]")
            if found is not None:
                return found
    return None


def serialize_rust_ast(ast, access_path="", parent=None) -> list:
    """Serialize a Rust AST into a list of RustASTNode objects.

    Args:
        ast: The AST data structure to serialize (dict or list).
        access_path: The current access path for nested elements (default: "").
        parent: The parent RustASTNode object (default: None).

    Returns:
        List of RustASTNode objects representing the serialized AST.
    """
    nodes = []
    if isinstance(ast, dict):
        mut_target_path = None
        # Match - include nodes that has src and ident keys
        if "src" in ast and "ident" in ast:
            metadata = {}
            if "mut" in ast:
                metadata["mut"] = ast["mut"]
            node = RustASTNode(ast, access_path, metadata)
            node.parent = parent
            nodes.append(node)
            parent = node

        # Mutable but no ident edge case, correlate a mutable statement with the
        # closest ident.
        #
        # `&mut expr` puts the mutability on a wrapper dict that carries no ident
        # of its own, so the flag has to be attached to a node further down. This
        # used to emit a *second* node at that node's access path, and the twin
        # was ruinous: `parse_rust_ast` indexes nodes by access path, so the twin
        # displaced the real node in the index, and the whole subtree beneath it
        # - the receiver chain of `&mut info.data.borrow_mut()`, every field of
        # `&mut ctx.accounts.vault.amount` - was linked to a node that was itself
        # unreachable from the root, and vanished from the tree the rules walk.
        # A rule could see `borrow_mut` but never which account it borrowed.
        #
        # The flag is now merged onto the node the main walk builds, after that
        # walk has run. One node per access path, and `mut` lands on a node the
        # rules can actually reach - which `find_mutables` also depends on.
        elif "mut" in ast:
            mut_target_path = _find_ident_src_path(ast, access_path)

        # Capture binary operator information
        if "op" in ast and parent:
            if not hasattr(parent, "metadata"):
                parent.metadata = {}
            parent.metadata["op"] = ast["op"]

        # Also capture operator from binary expressions (syn AST structure)
        if "binary" in ast and isinstance(ast["binary"], dict) and "op" in ast["binary"]:
            # Find the first ident node in the left side to use its src location
            def find_first_ident_node(data, path):
                if isinstance(data, dict):
                    if "src" in data and "ident" in data:
                        return (data, path)
                    for key, value in data.items():
                        result = find_first_ident_node(value, f"{path}.{key}" if path else key)
                        if result:
                            return result
                elif isinstance(data, list):
                    for i, item in enumerate(data):
                        result = find_first_ident_node(item, f"{path}[{i}]")
                        if result:
                            return result
                return None
            
            # Create a node for the binary operator
            left_result = find_first_ident_node(ast["binary"].get("left", {}), "")
            if left_result:
                left_node_data, _ = left_result
                binary_op = ast["binary"]["op"]
                binary_node_data = {
                    "src": left_node_data["src"],
                    "ident": binary_op
                }
                binary_node = RustASTNode(
                    binary_node_data,
                    f"{access_path}.binary",
                    {"op": binary_op}
                )
                binary_node.parent = parent
                nodes.append(binary_node)

        # Look deeper
        for key, value in ast.items():
            new_path = f"{access_path}.{key}" if access_path else key
            nodes.extend(serialize_rust_ast(value, new_path, parent))

        if mut_target_path is not None:
            for candidate in nodes:
                if candidate.access_path == mut_target_path:
                    candidate.metadata["mut"] = ast["mut"]
                    break
    
    # Look deeper
    elif isinstance(ast, list):
        for i, item in enumerate(ast):
            new_path = f"{access_path}[{i}]"
            nodes.extend(serialize_rust_ast(item, new_path, parent))

    return nodes


def parse_ast(ast: dict, language: str = "rust") -> dict:
    """Parse an AST dictionary into organized source-based node hierarchies.

    Args:
        ast: The AST dictionary to parse.
        language: Programming language ('rust' or 'solidity'). Defaults to 'rust'.

    Returns:
        Dictionary mapping source file names to their root ASTNode objects.
    """
    if language == "solidity":
        from utils.dsl.solidity import parse_solidity_ast
        return parse_solidity_ast(ast)
    else:
        return parse_rust_ast(ast)


def parse_rust_ast(ast: dict) -> dict:
    """Parse Rust AST dictionary into organized source-based node hierarchies.

    Args:
        ast: The Rust AST dictionary to parse.

    Returns:
        Dictionary mapping source file names to their root RustASTNode objects.
    """
    sources = {}
    nodes = serialize_rust_ast(ast)

    for node in nodes:
        source = node.src.get("file") if node.src else "unknown"
        if source not in sources:
            sources[source] = []
        sources[source].append(node)

    roots = {}
    for source, nodes in sources.items():
        # First node wins an access path. Paths are meant to be unique; where a
        # shape still produces two, indexing the later one would point every
        # descendant at a node that is not itself linked into the tree, and the
        # whole subtree would drop out silently.
        path_to_node = {}
        for node in nodes:
            path_to_node.setdefault(node.access_path, node)

        # Keyed by identity, not by access path: two nodes sharing a path are
        # still two nodes, and skipping the second used to strand it.
        attached = set()
        for node in nodes:
            parent_path = ".".join(node.access_path.split(".")[:-1])
            while parent_path:
                parent_node = path_to_node.get(parent_path)
                if parent_node is not None and parent_node is not node:
                    parent_node.add_child(node)
                    attached.add(id(node))
                    break
                parent_path = ".".join(parent_path.split(".")[:-1])

        root = RustASTNode()
        root._all_nodes = nodes
        for node in nodes:
            node._all_nodes = nodes
            # A node that found no parent belongs to the root. Testing
            # `node.parent` here instead would consult the pointer serialization
            # already set, which is almost always non-empty, so an unlinked node
            # was neither a child of anything nor a child of the root: it existed
            # in the flat list and was unreachable from the tree every rule walks.
            if id(node) not in attached:
                root.add_child(node)
        roots[source] = root

    return roots
