package main

import (
	"bufio"
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"strconv"
	"strings"

	"gopkg.in/yaml.v3"
)

const logo = `░██████╗░░█████╗░███████╗██╗░░░░░░█████╗░██████╗░
██╔════╝░██╔══██╗██╔════╝██║░░░░░██╔══██╗██╔══██╗
██║░░██╗░██║░░██║█████╗░░██║░░░░░███████║██████╔╝
██║░░╚██╗██║░░██║██╔══╝░░██║░░░░░██╔══██║██╔═══╝░
╚██████╔╝╚█████╔╝██║░░░░░███████╗██║░░██║██║░░░░░
░╚═════╝░░╚════╝░╚═╝░░░░░╚══════╝╚═╝░░╚═╝╚═╝░░░░░`

type PDA_transition struct {
	StartState int
	Character  string
	Pop        string
	Push       string
	FinalState int
}

type PDA_settings struct {
	//Q []int `yaml:"Q"`
	//Sigma []string `yaml:"Sigma"`
	//Gamma []string `yaml:"Gamma"`
	Delta string `yaml:"Delta"`
	Q0    int    `yaml:"q0"`
	Z     string `yaml:"Z"`
	F     []int  `yaml:"F"`
}

type PDA struct {
	Stack       []string
	State       int
	Settings    PDA_settings
	Transitions []PDA_transition
}

// start, char, pop, push, end
// each 5 elements constructs one transition

// stack designed so the right side is pushed and popped
// unlike JFLAP graphical representation

func create_pda(settings PDA_settings) PDA {
	pda := PDA{}

	pda.Stack = append(pda.Stack, settings.Z)
	pda.State = settings.Q0
	pda.Settings = settings

	s := strings.TrimSpace(settings.Delta)
	s = strings.Replace(s, ", ", " ", -1)
	s = strings.Replace(s, ",", " ", -1)
	v := strings.Split(s, " ")
	//fmt.Println(v)

	var transition PDA_transition
	for i := 0; i <= len(v)-5; i += 5 {
		transition = PDA_transition{}
		startstate, _ := strconv.Atoi(v[i])
		transition.StartState = startstate
		transition.Character = v[i+1]
		transition.Pop = v[i+2]
		transition.Push = v[i+3]
		finalstate, _ := strconv.Atoi(v[i+4])
		transition.FinalState = finalstate
		pda.Transitions = append(pda.Transitions, transition)
	}

	//fmt.Println(pda.Transitions)
	return pda
}

func find_transitions_pda(pda *PDA, character string) []PDA_transition {
	state := pda.State
	stack := pda.Stack
	transitions := []PDA_transition{}

	for _, transition := range pda.Transitions {
		if transition.StartState == state && (transition.Character == character || transition.Character == "λ") {
			if transition.Pop == "λ" || transition.Pop == stack[len(stack)-1] {
				transitions = append(transitions, transition)
			}
		}
	}
	return transitions
}

// Returns (1) false if it can't continue on this step
// Returns (2) false if it didn't consume the input character, true if it did
func step_pda(pda *PDA, character string, verbose bool) (bool, bool) {
	transitions := find_transitions_pda(pda, character)
	transition_index := 0

	if len(transitions) == 0 {
		return false, false
	}
	if len(transitions) > 1 {
		fmt.Println("!WARNING! Non determinism detected", len(transitions))

		fmt.Println("Choose a transition to continue:")
		for i, t := range transitions {
			fmt.Printf("%d: ", i)
			print_transition(&t)
		}

		fmt.Scanf("%d\n", &transition_index)
	}

	transition := transitions[transition_index]

	if verbose {
		fmt.Printf("Transition: ")
		print_transition(&transition)
	}

	if transition.Pop != "λ" {
		pda.Stack = pda.Stack[:len(pda.Stack)-1]
	}
	if transition.Push != "λ" {
		/* support for multiple character push down */
		for _, char := range transition.Push {
			pda.Stack = append(pda.Stack, string(char))
		}
		//pda.Stack = append(pda.Stack, transition.Push)

	}
	pda.State = transition.FinalState

	return true, transition.Character != "λ"
}

func run_pda(pda PDA, input string, verbose bool) bool {
	var do_continue bool = true
	var consume_input bool
	input_index := 0
	var char string

	for do_continue {
		if input_index < len(input) {
			char = string(input[input_index])
		} else {
			char = ""
		}
		do_continue, consume_input = step_pda(&pda, char, verbose)
		if consume_input {
			input_index++
		}
		if do_continue && verbose {
			fmt.Println(pda.Stack)
		}
	}

	if int_in_slice(pda.State, pda.Settings.F) && input_index == len(input) {
		return true
	}
	return false
}

func check_err(err error) {
	if err != nil {
		log.Fatal(err)
	}
}

func int_in_slice(n int, arr []int) bool {
	for _, num := range arr {
		if num == n {
			return true
		}
	}
	return false
}

func print_transition(transition *PDA_transition) {
	fmt.Printf("State: %d | %s -> %s ; %s | State: %d\n", transition.StartState,
		transition.Character,
		transition.Pop,
		transition.Push,
		transition.FinalState)
}

type GOFLAP_State struct {
	PushDownAutomata PDA
	Loaded           bool
}

func load_command(arg string, state *GOFLAP_State) {
	pda_settings := PDA_settings{}

	yfile, err := ioutil.ReadFile("inputs/" + arg)
	if err != nil {
		fmt.Println("Error loading file inputs/" + arg)
		return
	}

	pda_settings.Q0 = -1234

	err = yaml.Unmarshal(yfile, &pda_settings)
	if err != nil {
		fmt.Println(err)
		return
	}

	if pda_settings.Z == "" {
		fmt.Println("No stack start character specified, defaulting to \"Z\"")
		pda_settings.Z = "Z"
	}

	if pda_settings.Q0 == -1234 {
		fmt.Println("No initial state specified, defaulting to 0")
		pda_settings.Q0 = 0
	}

	if len(pda_settings.F) == 0 {
		fmt.Println("Warning: No final states specified, this machine won't accept anything")
	}

	pda := create_pda(pda_settings)
	state.PushDownAutomata = pda
	state.Loaded = true

	fmt.Println("Successfully loaded file inputs/" + arg + " as PDA")
}

func base_run_command(arg string, state *GOFLAP_State, verbose bool) {
	if !state.Loaded {
		fmt.Println("Run what? You haven't loaded anything yet.")
		return
	}

	result := run_pda(state.PushDownAutomata, arg, verbose)
	if result {
		fmt.Printf("Input `%s` is in the language defined by the PDA\n", arg)
	} else {
		fmt.Printf("Input `%s` is not in the language defined by the PDA\n", arg)
	}
}

func run_command(arg string, state *GOFLAP_State) {
	base_run_command(arg, state, false)
}

func runv_command(arg string, state *GOFLAP_State) {
	base_run_command(arg, state, true)
}

func inspect_command(arg string, state *GOFLAP_State) {
	if !state.Loaded {
		fmt.Println("Inspect what? You haven't loaded anything yet.")
		return
	}

	pda := state.PushDownAutomata

	fmt.Print("Start Stack: ")
	fmt.Println(pda.Stack)

	fmt.Printf("Start State: %d\n", pda.State)

	fmt.Print("Final State(s): ")
	fmt.Println(pda.Settings.F)

	fmt.Println("")

	fmt.Println("Transitions:")
	if len(pda.Transitions) == 0 {
		fmt.Println("None")
	} else {
		for _, transition := range pda.Transitions {
			print_transition(&transition)
		}
	}
}

func exit_command(arg string, state *GOFLAP_State) {
	os.Exit(0)
}

func help_command(arg string, state *GOFLAP_State) {
	fmt.Println("GOFLAP commands:")
	fmt.Println("Use the `load (file)` command to open PDA files from the inputs folder")
	fmt.Println("Use the `run (input)` command to run the currently loaded PDA")
	fmt.Println("        `runv (input)` for a verbose run")
	fmt.Println("Use the `inspect` command to view the currently loaded PDA")
	fmt.Println("Use the `exit` command to stop the program")
	fmt.Println("Use the `help` command to summon this prompt")
}

func charlie_command(arg string, state *GOFLAP_State) {
	if arg == "Hayden" {
		fmt.Println("What a guy")
	} else if arg != "" {
		fmt.Println("Charlie who?")
	} else {
		fmt.Println("What about him?")
	}
}

//current problems:
//multiple push characters?

func main() {
	var input string
	var raw_tokens []string
	var tokens []string
	var command_in string
	var command_arg string
	var command_recognized bool
	//var err error
	state := GOFLAP_State{}
	scanner := bufio.NewScanner(os.Stdin)

	fmt.Println(logo)
	fmt.Println("Welcome to GOFLAP CLI")
	fmt.Println("")
	help_command("", &state)

	commands := make(map[string]func(string, *GOFLAP_State))
	commands["load"] = load_command
	commands["exit"] = exit_command
	commands["help"] = help_command
	commands["run"] = run_command
	commands["runv"] = runv_command
	commands["Charlie"] = charlie_command
	commands["inspect"] = inspect_command

	for true {
		fmt.Println("")
		fmt.Print("GOFLAP>")

		if scanner.Scan() {
			input = scanner.Text()
		}

		tokens = nil
		raw_tokens = strings.Split(input, " ")
		for _, token := range raw_tokens {
			if token != "" {
				tokens = append(tokens, token)
			}
		}

		command_recognized = true
		if len(tokens) == 0 {
			fmt.Println("Huh?")
			command_recognized = false
		} else if len(tokens) == 1 {
			command_in = tokens[0]
			command_arg = ""
		} else if len(tokens) == 2 {
			command_in = tokens[0]
			command_arg = tokens[1]
		} else {
			fmt.Println("Too many tokens, GOFLAP commands only have `command` and `argument`")
			command_recognized = false
		}

		if command_recognized {
			command_recognized = false
			for command, function := range commands {
				if command_in == command {
					function(command_arg, &state)
					command_recognized = true
					break
				}
			}

			if !command_recognized {
				fmt.Printf("Unrecognized command `%s` from input `%s`\n", command_in, input)
			}
		}
	}
}
