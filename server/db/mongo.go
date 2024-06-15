package db

import (
	"context"
	"errors"
	"fmt"
	"sync"
	"time"

	"github.com/npi-ai/npi/server/api"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
	"go.mongodb.org/mongo-driver/mongo/readpref"
	"go.mongodb.org/mongo-driver/mongo/writeconcern"
)

// below are general available
const (
	CollTools           = "tools"
	CollToolSpec        = "tool_specs"
	CollToolInstance    = "tool_instances"
	CoolDistributedLock = "distributed_lock"
)

type MongoConfig struct {
	Address       string `yaml:"address"`
	Database      string `yaml:"database"`
	Username      string `yaml:"username"`
	Password      string `yaml:"password"`
	AuthMechanism string `yaml:"auth_mechanism"`
	PemFile       string `yaml:"pem_file"`
}

func (c MongoConfig) GetURI() string {
	if c.AuthMechanism == "MONGODB-X509" {
		return fmt.Sprintf(
			"mongodb+srv://%s/?authSource=$external&authMechanism=MONGODB-X509&retryWrites=true&w=majority&tlsCertificateKeyFile=%s",
			c.Address, c.PemFile)
	}
	return fmt.Sprintf(
		"mongodb+srv://%s:%s@%s/?retryWrites=true&w=majority",
		c.Username, c.Password, c.Address)
}

var (
	mutex    sync.Mutex
	cli      *mongo.Client
	collMap  = make(map[string]*mongo.Collection)
	mongoCfg MongoConfig
)

func GetCollection(name string) *mongo.Collection {
	mutex.Lock()
	defer mutex.Unlock()
	coll, ok := collMap[name]
	if !ok {
		coll = cli.Database(mongoCfg.Database).Collection(name)
		collMap[name] = coll
	}
	return coll
}

func GetClient() *mongo.Client {
	return cli
}

func InitMongoDB(ctx context.Context, cfg MongoConfig) {
	mongoCfg = cfg
	clientOptions := options.Client().
		ApplyURI(cfg.GetURI()).
		SetServerAPIOptions(options.ServerAPI(options.ServerAPIVersion1))
	ctx, cancel := context.WithTimeout(ctx, 30*time.Second)
	defer cancel()
	var err error
	cli, err = mongo.Connect(ctx, clientOptions)

	if err != nil {
		panic(err)
	}

	if err = cli.Ping(ctx, readpref.Primary()); err != nil {
		panic(err)
	}
}

func ConvertError(err error) error {
	if err == nil {
		return nil
	}
	if errors.Is(err, mongo.ErrNoDocuments) {
		return api.DocumentNotFound
	}
	return err
}

func NewSession() (mongo.Session, error) {
	return cli.StartSession()
}

func WithTransaction(ctx context.Context, callback func(sessionCtx mongo.SessionContext) (interface{}, error)) error {
	ss, err := NewSession()
	if err != nil {
		return ConvertError(err)
	}
	defer ss.EndSession(ctx)

	if _, err = ss.WithTransaction(ctx, callback, TransactionOptions()); err != nil {
		return err
	}
	return nil
}

func TransactionOptions() *options.TransactionOptions {
	return options.Transaction().SetWriteConcern(
		writeconcern.New(writeconcern.WMajority()),
	)
}
