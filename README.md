# Secure Distributed Dice Game (PoC)

## Overview
This project implements a secure, distributed dice game between two parties (Alice and Bob) using a **Commit-then-Reveal** protocol to ensure fairness without a Trusted Third Party. The application is containerized using Docker to simulate two distinct nodes communicating over TCP.

**Course:** Cybersecurity (Sapienza University of Rome)  
**Author:** Jacopo Rossi

## Features
- **Fairness:** Uses SHA-256 Commitments and XOR-based seed derivation ($S = N_A \oplus N_B$).
- **Isolation:** Each player runs in a separate Docker container.
- **Robustness:** Client implements a retry mechanism to handle connection timing.

## Prerequisites
- Docker & Docker Compose

## How to Run

1. **Start the Environment**
   ```bash
   docker compose up -d --build
   '''

2. **See the output**
   **Alice(Server)**
   Attach to Alice's container to set game parameters
   '''bash
   docker attach alice_vm
   '''

   **Bob(Client)**
   Open a new terminal to view Bob's output (He connects automatically)
   '''bash
   docker logs -f bob_vm'''

3. **Shutdown**
   '''bash
   docker compose down'''