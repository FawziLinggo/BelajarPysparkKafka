package main

import (
	"database/sql"
	"encoding/json"
	"log"
	"net/http"
	"strconv"

	_ "github.com/denisenkom/go-mssqldb"
	"github.com/gorilla/mux"
)

var (
	db *sql.DB
	username = "username"
	password = "password"
	server = "192.168.35.80"
	port = 1433
	database = "fawzi"
)

func connect() {
    var err error
    db, err = sql.Open("mssql", "server="+server+";user id="+username+";password="+password+";port="+strconv.Itoa(port)+";database="+database)
    if err != nil {
        log.Fatal(err)
    }
}

type Data struct {
    ID       int    `json:"id"`
    Name     string `json:"name"`
    Kategory string `json:"kategory"`
}

func createData(w http.ResponseWriter, r *http.Request) {
    var data Data
    err := json.NewDecoder(r.Body).Decode(&data)
    if err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }
    defer r.Body.Close()

    query := "INSERT INTO dbo.data (name, kategory) VALUES (?, ?); SELECT SCOPE_IDENTITY()"
	row := db.QueryRow(query, data.Name, data.Kategory)

	var id int
	err = row.Scan(&id)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

    data.ID = int(id)

    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(data)
}

func readData(w http.ResponseWriter, r *http.Request) {
    params := mux.Vars(r)
    id := params["id"]

    var data Data
    query := "SELECT id, name, kategory FROM dbo.data WHERE id = ?"
    row := db.QueryRow(query, id)
    err := row.Scan(&data.ID, &data.Name, &data.Kategory)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }

    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(data)
}

func updateData(w http.ResponseWriter, r *http.Request) {
    params := mux.Vars(r)
    id := params["id"]

    var data Data
    err := json.NewDecoder(r.Body).Decode(&data)
    if err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }
    defer r.Body.Close()

    query := "UPDATE dbo.data SET name = ?, kategory = ? WHERE id = ?"
    _, err = db.Exec(query, data.Name, data.Kategory, id)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }

    data.ID, _ = strconv.Atoi(id)

    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(data)
}

func deleteData(w http.ResponseWriter, r *http.Request) {
    params := mux.Vars(r)
    id := params["id"]

    query := "DELETE FROM dbo.data WHERE id = ?"
    _, err := db.Exec(query,  id)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }

    w.WriteHeader(http.StatusNoContent)
}


func main() {
    connect()

    router := mux.NewRouter()

    router.HandleFunc("/data", createData).Methods("POST")
    router.HandleFunc("/data/{id}", readData).Methods("GET")
    router.HandleFunc("/data/{id}", updateData).Methods("PUT")
    router.HandleFunc("/data/{id}", deleteData).Methods("DELETE")

    log.Fatal(http.ListenAndServe(":4321", router))
}
