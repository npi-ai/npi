package model

import (
	"encoding/base64"
	"encoding/json"
	"github.com/markbates/goth/providers/github"
	"go.mongodb.org/mongo-driver/bson/primitive"
	"golang.org/x/oauth2"
	"os"
)

type AppCode string

func (ac AppCode) Name() string {
	return string(ac)
}

const (
	AppGitHub         = AppCode("GITHUB")
	AppDiscord        = AppCode("DISCORD")
	AppXCom           = AppCode("TWITTER")
	AppSlack          = AppCode("SLACK")
	AppTwilio         = AppCode("TWILIO")
	AppGoogleGmail    = AppCode("GOOGLE_GMAIL")
	AppGoogleCalendar = AppCode("GOOGLE_CALENDAR")
)

type AppClient struct {
	Base        `json:",inline" bson:",inline"`
	TenantID    primitive.ObjectID `json:"tenant_id" bson:"tenant_id"`
	UserID      primitive.ObjectID `json:"user_id" bson:"user_id"`
	Name        string             `json:"name" bson:"name"`
	ClientID    string             `json:"client_id" bson:"client_id"`
	Secrets     []string           `json:"secrets" bson:"secrets"`
	RedirectURL []string           `json:"redirect_urls" bson:"redirect_urls"`
	UserDefault bool               `json:"-" bson:"user_default,omitempty"`
}

type AuthUserToNPI struct {
	Base         `json:"-" bson:",inline"`
	UserID       primitive.ObjectID `json:"-" bson:"user_id"`
	AuthID       primitive.ObjectID `json:"-" bson:"auth_id"`
	AppUserID    string             `json:"-" bson:"app_user_id"`
	PermissionID int                `json:"-" bson:"permission"`
}

type UserAuthorization struct {
	Base         `json:"-" bson:",inline"`
	Code         AppCode `json:"-" bson:"app_code"`
	Credentials  []byte  `json:"-" bson:"credentials"`
	PermissionID int     `json:"-" bson:"permission"`
}

func (ua UserAuthorization) GenerateCredentials(cfg *oauth2.Config, token *oauth2.Token) []byte {
	data, _ := json.Marshal(token)
	switch ua.Code {
	case AppGoogleGmail, AppGoogleCalendar:
		m := map[string]interface{}{}
		_ = json.Unmarshal(data, &m)
		m["client_id"] = cfg.ClientID
		m["client_secret"] = cfg.ClientSecret
		data, _ = json.Marshal(m)
	}
	return data
}

func (ua UserAuthorization) Authorization() string {
	var token string
	switch ua.Code {
	case AppGitHub:
		m := map[string]string{}
		_ = json.Unmarshal(ua.Credentials, &m)
		token = m["access_token"]
	case AppDiscord:
		token = os.Getenv("DISCORD_BOT_TOKEN")
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
	Fields       []Field  `json:"fields" bson:"fields"`
}

type Field struct {
	Key         string `json:"key" bson:"key"`
	DisplayName string `json:"display_name"`
	Description string `json:"description"`
}

func (p Permission) IsGoogle() bool {
	return p.PermissionID > 100001000 && p.PermissionID < 110001000
}

func GetPermission(id int) Permission {
	perm := permissions[id]
	return perm
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
		AuthMethod:   AuthOAuth,
		Scopes:       nil,
		Name:         "github:all",
		Description:  "get the all permissions of GitHub",
	}

	AppDiscordAll = Permission{
		PermissionID: 10001001, // 1000, between two app permission id range
		Code:         AppDiscord,
		AuthMethod:   AuthOAuth,
		Scopes:       []string{"messages.read", "bot"},
		Name:         "discord:all",
		Description:  "",
	}

	AppXComAll = Permission{
		PermissionID: 10003001, // 1000, between two app permission id range
		Code:         AppXCom,
		Scopes:       nil,
		AuthMethod:   AuthPassword,
		Name:         "xcom:all",
		Description:  "get the all permissions of GitHub",
		Fields: []Field{
			{
				Key:         "username",
				DisplayName: "Username",
			},
			{
				Key:         "password",
				DisplayName: "Password",
			},
		},
	}

	AppSlackAll = Permission{
		PermissionID: 10004001, // 1000, between two app permission id range
		Code:         AppSlack,
		AuthMethod:   AuthOAuth,
		Scopes:       nil,
		Name:         "slack:all",
		Description:  "get the all permissions of GitHub",
	}

	AppTwilioAll = Permission{
		PermissionID: 10005001, // 1000, between two app permission id range
		Code:         AppTwilio,
		Scopes:       nil,
		AuthMethod:   AuthAPIKey,
		Name:         "twilio:all",
		Description:  "get the all permissions of GitHub",
		Fields: []Field{
			{
				Key:         "sid",
				DisplayName: "Account SID",
			},
			{
				Key:         "token",
				DisplayName: "Account Token",
			},
			{
				Key:         "phone_number",
				DisplayName: "From Number",
			},
		},
	}

	AppGoogleGmailAll = Permission{
		PermissionID: 100001001,
		Code:         AppGoogleGmail,
		AuthMethod:   AuthOAuth,
		Scopes:       []string{"https://mail.google.com/"},
		Name:         "google:gmail:all",
		Description:  "get the all permissions of GitHub",
	}

	AppGoogleCalendarAll = Permission{
		PermissionID: 100002001,
		Code:         AppGoogleCalendar,
		AuthMethod:   AuthOAuth,
		Scopes:       []string{"https://www.googleapis.com/auth/calendar"},
		Name:         "google:calender:all",
		Description:  "get the all permissions of GitHub",
	}
)

var (
	appOAuthEndpoint = map[AppCode]oauth2.Endpoint{
		AppGitHub: {
			AuthURL:   github.AuthURL,
			TokenURL:  github.TokenURL,
			AuthStyle: oauth2.AuthStyleAutoDetect,
		},
		AppDiscord: {
			AuthURL:   "https://discord.com/api/oauth2/authorize",
			TokenURL:  "https://discord.com/api/oauth2/token",
			AuthStyle: oauth2.AuthStyleAutoDetect,
		},
		AppSlack: {
			AuthURL:   "https://slack.com/oauth/authorize",
			TokenURL:  "https://slack.com/api/oauth.access",
			AuthStyle: oauth2.AuthStyleAutoDetect,
		},
		AppGoogleCalendar: googleEndpoint,
		AppGoogleGmail:    googleEndpoint,
	}
)

var (
	googleEndpoint = oauth2.Endpoint{
		AuthURL:       "https://accounts.google.com/o/oauth2/auth",
		TokenURL:      "https://oauth2.googleapis.com/token",
		DeviceAuthURL: "https://oauth2.googleapis.com/device/code",
		AuthStyle:     oauth2.AuthStyleInParams,
	}
)

func GetOAuthEndpoint(code AppCode) oauth2.Endpoint {
	return appOAuthEndpoint[code]
}
