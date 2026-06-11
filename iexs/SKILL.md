---
name: iexs
description: >
  Generates Elixir scripts formatted for copy-paste into an IEx (Interactive Elixir) REPL session.
  Use this skill whenever the user asks for IEx-compatible code, an iex script, something to run in
  iex, or wants to quickly test/explore Elixir code interactively. Trigger even when the user says
  things like "give me elixir code to try", "how do i test this in elixir", "write a quick elixir
  snippet", "elixir one-liner", or pastes Elixir code and asks to make it iex-compatible.
  Never output Elixir scripts for iex without consulting this skill — vanilla code generation
  frequently produces formatter-styled pipes and unaliased modules that silently fail in IEx.
---

# IEx Script Generator

You are generating Elixir code meant to be copy-pasted into an `iex` session. This is different from writing a `.exs` file or a Mix project — the code runs in an interactive REPL that evaluates expressions one at a time, which creates specific constraints.

## The core problem: why vanilla Elixir code breaks in IEx

IEx reads your input and decides when an expression is "complete" before evaluating it. This causes two common breakage patterns:

**1. Bare pipes break silently**
```elixir
# This fails in IEx — it evaluates [1,2,3] first, then errors on |> Enum.map(...)
[1, 2, 3]
|> Enum.map(fn x -> x * 2 end)
|> Enum.sum()
```
IEx sees `[1, 2, 3]` as a complete expression and evaluates it immediately. The next line `|> Enum.map(...)` then has no left-hand side and fails.

**2. Unaliased modules cause confusion**
In a Mix project, `alias MyApp.Repo` is set up by the app. In a plain `iex` session, you get nothing for free — every module must be fully qualified unless you alias it explicitly at the start.

## Rules for IEx-safe code

### Pipes: wrap or eliminate

**Option A — wrap the whole chain in parentheses:**
```elixir
(
  [1, 2, 3]
  |> Enum.map(fn x -> x * 2 end)
  |> Enum.sum()
)
```
IEx sees the opening `(` and waits for the matching `)` before evaluating — the pipe chain is safe.

**Option B — flatten to nested calls (preferred for short chains):**
```elixir
Enum.sum(Enum.map([1, 2, 3], fn x -> x * 2 end))
```
No pipes, no ambiguity.

Choose whichever reads more clearly. For long chains (4+ steps), wrapping in parentheses is usually cleaner than deep nesting. For 1-2 steps, nested calls are usually simpler.

### Module names: alias at top or fully qualify everywhere

At the top of the script, add any aliases you'll need:
```elixir
alias Ecto.Changeset
alias MyApp.{Repo, User}
import Ecto.Query, only: [from: 2, where: 3]
```

Or just use fully qualified names throughout:
```elixir
Ecto.Changeset.cast(changeset, attrs, fields)
MyApp.Repo.all(MyApp.User)
```

Mixing strategies is fine — alias the modules you use heavily, fully qualify ones used once.

### Multi-line blocks are fine

`do...end` blocks, `fn...end`, `case`, `cond`, `with` — IEx waits for these to close before evaluating. You don't need to do anything special:
```elixir
result = case Map.get(map, :key) do
  nil -> :not_found
  val -> {:ok, val}
end
```

### Variable bindings persist across pastes

Each expression you paste into IEx can use variables bound in earlier expressions. You can structure your script as a series of pastes, where later sections build on earlier ones. Make this explicit in your output when relevant.

## Output format

Produce a script the user can copy-paste. Use one of these formats based on what fits:

**Single block to paste all at once:**
```elixir
# Setup
alias Enum, as: E

data = [1, 2, 3, 4, 5]

result = E.reduce(data, 0, fn x, acc -> acc + x end)
IO.inspect(result, label: "sum")
```

**Numbered sections for interactive exploration:**
When the task benefits from seeing intermediate results, split into numbered sections with a comment explaining what each does and what to expect:
```elixir
# Step 1: Load and inspect the data
data = [%{name: "Alice", age: 30}, %{name: "Bob", age: 25}]
IO.inspect(data, label: "data")

# Step 2: Filter adults over 28
filtered = Enum.filter(data, fn person -> person.age > 28 end)
IO.inspect(filtered, label: "filtered")
```

## Common patterns

**String operations:**
```elixir
name = "hello world"
upcased = String.upcase(name)
words = String.split(name, " ")
IO.inspect({upcased, words})
```

**Enum transformations (pipe-safe with wrapping):**
```elixir
result = (
  1..10
  |> Enum.filter(fn n -> rem(n, 2) == 0 end)
  |> Enum.map(fn n -> n * n end)
)
IO.inspect(result)
```

**Map operations:**
```elixir
m = %{a: 1, b: 2, c: 3}
updated = Map.put(m, :d, 4)
keys = Map.keys(updated)
IO.inspect({updated, keys})
```

**Struct creation (alias required):**
```elixir
# If using a struct from your app, alias first:
# alias MyApp.User
# Then:
# user = %MyApp.User{name: "Alice", email: "alice@example.com"}
```

## What NOT to do

- Don't write bare pipe chains that start on one line and continue on the next without wrapping
- Don't assume module aliases exist — always alias explicitly or fully qualify
- Don't use `Mix.install/1` unless the user is on Elixir 1.12+ and explicitly running a script file; it's not needed for core library exploration
- Don't add `defmodule` wrappers unless the user specifically needs to define a module to test
- Don't add unnecessary `Application.ensure_all_started(:my_app)` — call it only if the user's context requires a running OTP app

## Checking your output

Before finishing, mentally simulate running each line in IEx:
1. Would IEx consider this expression complete before reaching the next line?
2. Are all module names either aliased or fully qualified?
3. Is the output self-contained — can it be pasted in one go and work?
