from automata import DFA, NFA

def construct_dfa_from_user():
    dfa = DFA()

    print("Enter DFA states (comma separated):")
    states = input().split(",")
    for s in states:
        dfa.add_state(s.strip())
    
    print("Enter alphabet symbols (comma separated):")
    symbols = input().split(",")
    for sym in symbols:
        dfa.add_symbol(sym.strip())

    print("Enter start state:")
    dfa.set_start_state(input().strip())

    print("Enter accept states (comma separated):")
    accept_states = input().split(",")
    for acc in accept_states:
        dfa.add_accept_state(acc.strip())

    print("Enter transitions in format: from_state,symbol,to_state. Type 'done' to finish.")
    while True:
        line = input()
        if line.strip().lower() == "done":
            break
        parts = line.split(",")
        if len(parts) == 3:
            dfa.add_transition(parts[0].strip(), parts[1].strip(), parts[2].strip())
        else:
            print("Invalid format. Try again.")

    return dfa


def construct_nfa_from_user():
    nfa = NFA()

    print("Enter NFA states (comma separated):")
    states = input().split(",")
    for s in states:
        nfa.add_state(s.strip())

    print("Enter alphabet symbols (comma separated):")
    symbols = input().split(",")
    for sym in symbols:
        nfa.add_symbol(sym.strip())

    print("Enter start state:")
    nfa.set_start_state(input().strip())

    print("Enter accept states (comma separated):")
    accept_states = input().split(",")
    for acc in accept_states:
        nfa.add_accept_state(acc.strip())

    print("Enter transitions in format: from_state,symbol,to_state. Type 'done' to finish.")
    while True:
        line = input()
        if line.strip().lower() == "done":
            break
        parts = line.split(",")
        if len(parts) == 3:
            nfa.add_transition(parts[0].strip(), parts[1].strip(), parts[2].strip())
        else:
            print("Invalid format. Try again.")

    return nfa


def test_automaton_acceptance(automaton):
    while True:
        print("\nEnter string to test (or 'exit'):")
        string = input().strip()
        if string.lower() == "exit":
            break
        print("✅ Accepted" if automaton.accepts(string) else "❌ Rejected")


if __name__ == "__main__":
    print("Choose Automaton type:\n1. DFA\n2. NFA")
    choice = input().strip()

    if choice == "1":
        dfa = construct_dfa_from_user()
        test_automaton_acceptance(dfa)
    elif choice == "2":
        nfa = construct_nfa_from_user()
        test_automaton_acceptance(nfa)
    else:
        print("Invalid choice.")
