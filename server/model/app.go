package model

import (
	"encoding/base64"
	"encoding/json"
	"github.com/markbates/goth/providers/github"
	"go.mongodb.org/mongo-driver/bson/primitive"
	"golang.org/x/oauth2"
)

type AppCode string

func (ac AppCode) Name() string {
	return string(ac)
}

const (
	AppGitHub         = AppCode("github")
	AppDiscord        = AppCode("discord")
	AppXCom           = AppCode("xcom")
	AppSlack          = AppCode("slack")
	AppTwilio         = AppCode("twilio")
	AppGoogleGmail    = AppCode("gmail")
	AppGoogleCalendar = AppCode("google_calendar")
)

type AppClient struct {
	Base        `json:",inline" bson:",inline"`
	OrgID       primitive.ObjectID `json:"org_id" bson:"org_id"`
	Name        string             `json:"name" bson:"name"`
	ClientID    string             `json:"client_id" bson:"client_id"`
	Secrets     string             `json:"secrets" bson:"secrets"`
	RedirectURL []string           `json:"redirect_urls" bson:"redirect_urls"`
	APIKey      string             `json:"api_key" bson:"api_key"`
	OrgDefault  bool               `json:"-" bson:"org_default,omitempty"`
}

type AuthUserToNPI struct {
	Base      `json:"-" bson:",inline"`
	UserID    primitive.ObjectID `json:"-" bson:"user_id"`
	AuthID    primitive.ObjectID `json:"-" bson:"auth_id"`
	AppUserID string             `json:"-" bson:"app_user_id"`
}

type UserAuthorization struct {
	Base         `json:"-" bson:",inline"`
	Code         AppCode `json:"-" bson:"app_code"`
	Credentials  []byte  `json:"-" bson:"credentials"`
	PermissionID int     `json:"-" bson:"permission"`
}

func (ua UserAuthorization) Authorization() string {
	var token string
	switch ua.Code {
	case AppGitHub:
		m := map[string]string{}
		_ = json.Unmarshal(ua.Credentials, &m)
		token = m["access_token"]
	case AppSlack:
	case AppTwilio:
	case AppDiscord:
	default:
		token = string(ua.Credentials)
	}
	// TODO encrypt
	return base64.StdEncoding.EncodeToString([]byte(token))
}

type AuthNPIToApp struct {
	Base       `json:",inline" bson:",inline"`
	AppID      primitive.ObjectID `json:"-" bson:"app_id"`
	AuthID     primitive.ObjectID `json:"-" bson:"auth_id"`
	Permission int                `json:"-" bson:"permission"`
}

type Permission struct {
	PermissionID int      `json:"permission_id" bson:"permission_id"`
	AuthMethod   AuthType `json:"-" bson:"auth_method"`
	Code         AppCode  `json:"app_code" bson:"app_code"`
	Scopes       []string `json:"scopes" bson:"scopes"`
	Name         string   `json:"name" bson:"name"`
	Description  string   `json:"description" bson:"description"`
}

func (p Permission) IsGoogle() bool {
	return p.PermissionID > 100001000 && p.PermissionID < 110001000
}

func GetPermission(id int) Permission {
	return permissions[id]
}

var (
	permissions = map[int]Permission{
		AppGitHubAll.PermissionID:         AppGitHubAll,
		AppDiscordAll.PermissionID:        AppDiscordAll,
		AppXComAll.PermissionID:           AppXComAll,
		AppSlackAll.PermissionID:          AppSlackAll,
		AppTwilioAll.PermissionID:         AppTwilioAll,
		AppGoogleGmailAll.PermissionID:    AppGoogleGmailAll,
		AppGoogleCalendarAll.PermissionID: AppGoogleCalendarAll,
	}
)

var (
	AppGitHubAll = Permission{
		PermissionID: 10000001,
		Code:         AppGitHub,
		Scopes:       nil,
		Name:         "github:all",
		Description:  "get the all permissions of GitHub",
	}

	AppDiscordAll = Permission{
		PermissionID: 10001001, // 1000, between two app permission id range
		Code:         AppDiscord,
		Scopes:       nil,
		Name:         "discord:all",
		Description:  "get the all permissions of GitHub",
	}

	AppXComAll = Permission{
		PermissionID: 10003001, // 1000, between two app permission id range
		Code:         AppXCom,
		Scopes:       nil,
		Name:         "xcom:all",
		Description:  "get the all permissions of GitHub",
	}

	AppSlackAll = Permission{
		PermissionID: 10004001, // 1000, between two app permission id range
		Code:         AppSlack,
		Scopes:       nil,
		Name:         "slack:all",
		Description:  "get the all permissions of GitHub",
	}

	AppTwilioAll = Permission{
		PermissionID: 10005001, // 1000, between two app permission id range
		Code:         AppTwilio,
		Scopes:       nil,
		Name:         "twilio:all",
		Description:  "get the all permissions of GitHub",
	}

	AppGoogleGmailAll = Permission{
		PermissionID: 100001001,
		Code:         AppGoogleGmail,
		Scopes:       nil,
		Name:         "google:gmail:all",
		Description:  "get the all permissions of GitHub",
	}

	AppGoogleCalendarAll = Permission{
		PermissionID: 100002001,
		Code:         AppGoogleCalendar,
		Scopes:       nil,
		Name:         "google:calender:all",
		Description:  "get the all permissions of GitHub",
	}
)

var (
	appOAuthEndpoint = map[AppCode]*oauth2.Endpoint{
		AppGitHub: {
			AuthURL:   github.AuthURL,
			TokenURL:  github.TokenURL,
			AuthStyle: oauth2.AuthStyleAutoDetect,
		},
	}
)

func GetOAuthEndpoint(code AppCode) *oauth2.Endpoint {
	return appOAuthEndpoint[code]
}
