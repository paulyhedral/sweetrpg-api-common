package util

import (
	"math"

	"github.com/sweetrpg/api-core/constants"
	"github.com/sweetrpg/common/logging"
	dbconstants "github.com/sweetrpg/db/constants"
	options "go.jtlabs.io/query"
)

type QueryParams struct {
	Start int
	Limit int
}

func GetQueryParams(query string) QueryParams {
	logging.Logger.Debug("parsing query string", "query", query)

	opt, _ := options.FromQuerystring(query)
	logging.Logger.Debug("options from query string", "opt", opt)

	params := QueryParams{
		Start: int(math.Max(0, float64(opt.Page[constants.PageStartOption]))),
		Limit: int(math.Max(1, math.Min(float64(dbconstants.QueryMaxSize), float64(opt.Page[constants.PageLimitOption])))),
	}

	logging.Logger.Debug("final params", "params", params)
	return params
}
