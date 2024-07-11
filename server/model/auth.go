package model

type APIKeyProvider string

const (
	APIKeyProviderBuiltin = APIKeyProvider("builtin")
)

func (ap APIKeyProvider) AuthType() string {
	return "basic"
}

type APIKey struct {
	Base     `json:",inline" bson:",inline"`
	Provider APIKeyProvider `json:"provider" bson:"provider"`
	Value    string         `json:"value" bson:"value"`
}
